from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from hashlib import sha256
import json
from os import O_RDWR, O_WRONLY, fsdecode, name
from pathlib import Path
import sys
from uuid import uuid4
from zlib import ZLIB_RUNTIME_VERSION

sys.path.insert(0, str(Path(__file__).resolve().parent))

from VerifyMeasuredBox import (
    BOUNDS,
    EPOCH,
    FORMAT,
    LOCATOR,
    RECEIPT,
    RECEIPT_SHA,
    ROOT,
    SldprtWriter,
    WriteOptions,
    assert_result,
    box,
    fingerprint,
    prism,
    require,
    write_document,
)


@contextmanager
def lease(target, expected, preserve_existing):
    root = target.parent.parent
    for path in (root, target.parent, target):
        require(
            not (path.is_symlink() or path.is_junction()),
            "the measured output is not a direct task-owned path",
        )
    owned_root = False
    owned_parent = False
    backup = None
    if not root.exists():
        root.mkdir()
        owned_root = True
    try:
        if not target.parent.exists():
            target.parent.mkdir()
            owned_parent = True
        if target.exists():
            require(
                preserve_existing
                and target.is_file()
                and fingerprint(target.read_bytes()) == expected,
                "the measured output already contains an unrelated file",
            )
            held = target.with_name(f".held-{uuid4().hex}-{target.name}")
            target.rename(held)
            backup = held
        yield backup is not None
    finally:
        if backup is not None:
            if target.exists():
                target.rename(
                    target.with_name(f".retained-{uuid4().hex}-{target.name}")
                )
            backup.rename(target)
            require(
                fingerprint(target.read_bytes()) == expected,
                "the original disclosed output was not restored intact",
            )
        if owned_parent and target.parent.exists() and not any(target.parent.iterdir()):
            target.parent.rmdir()
        if owned_root and not any(root.iterdir()):
            root.rmdir()


@contextmanager
def audit_writer(target):
    allowed_code = (ROOT / "src", Path(sys.base_prefix), Path(sys.exec_prefix))
    reads = []
    active = True

    def audit(event, arguments):
        if not active:
            return
        if event.startswith(
            ("subprocess.", "socket.", "ctypes.", "winreg.")
        ) or event in {"os.system", "os.exec", "os.startfile"}:
            raise RuntimeError(f"publication attempted {event}")
        if event != "open":
            return
        location, _, flags = arguments
        if isinstance(location, int):
            return
        path = Path(fsdecode(location)).resolve()
        if flags & (O_WRONLY | O_RDWR) == O_WRONLY and path.is_relative_to(
            target.parent
        ):
            return
        if path.suffix in {".py", ".pyc"} and any(
            path.is_relative_to(root) for root in allowed_code
        ):
            return
        reads.append(str(path))
        raise RuntimeError(f"publication attempted to read {path.name}")

    sys.addaudithook(audit)
    try:
        yield reads
    finally:
        active = False


def prove(preserve_existing, profile="RectangularBare"):
    require(name == "nt", "the measured physical locator requires Windows")
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    raw = RECEIPT.read_bytes()
    require(sha256(raw).hexdigest() == RECEIPT_SHA, "the native receipt changed")
    receipt = json.loads(raw)
    case = receipt["cases"][profile]
    expected = {"bytes": case["generated_bytes"], "sha256": case["native_input_sha256"]}
    options = {
        "solidworks_native_measurement": {"written_at": EPOCH, "receipt": receipt}
    }
    if profile == "ConcaveOwned":
        from ConcaveImportCase import LOCATOR as CONCAVE_LOCATOR, OUTLINE, STATIONS

        target = Path(CONCAVE_LOCATOR)
        document = prism(OUTLINE, STATIONS)
        shape = "concave"
    else:
        target = Path(LOCATOR)
        document = box(BOUNDS)
        shape = "rectangular"
    publishers = {
        "registry": lambda: write_document(
            document,
            target,
            destination_format=FORMAT,
            allow_carrier=False,
            values=options,
        ),
        "direct": lambda: SldprtWriter().write(
            document, target, WriteOptions(values=options)
        ),
    }
    outcomes = {}
    with lease(target, expected, preserve_existing) as restored:
        for route, publish in publishers.items():
            with audit_writer(target) as reads:
                outcome = publish()
            assert_result(outcome)
            observed = fingerprint(target.read_bytes())
            require(
                not reads and observed == expected,
                f"{route} changed the measured archive",
            )
            outcomes[route] = observed
            target.unlink()
    return {
        "schema": f"kit.sw2026.measured-{shape}-import-windows-paths.v1",
        "exact_publications": len(outcomes),
        "runtime_input_file_reads": 0,
        "runtime": {"python": list(sys.version_info[:3]), "zlib": ZLIB_RUNTIME_VERSION},
        "native_processes_started": 0,
        "declared_locator_option_used": False,
        "original_locator_restored": restored,
        "routes": outcomes,
        "native_receipt_sha256": RECEIPT_SHA,
    }


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--preserve-existing-measured-output", action="store_true")
    cli.add_argument(
        "--profile",
        choices=("RectangularBare", "ConcaveOwned"),
        default="RectangularBare",
    )
    args = cli.parse_args()
    print(
        json.dumps(
            prove(args.preserve_existing_measured_output, args.profile),
            indent=2,
            sort_keys=True,
        )
    )
