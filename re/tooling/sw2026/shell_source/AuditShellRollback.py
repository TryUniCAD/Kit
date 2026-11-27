from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
ARCHIVE_PIN = "31254df08b173d8cd218cf6b0b81b9703ae23fea"
KERNEL_PIN = "0167c3e33a045b82fb9ac17a5aa10560b2070ba8"
RECEIPT = "d469a4d75549f1c95948047264c118adadb3b843b3376218140baa61c752987b"
CASES = {
    "OpenShell.SLDPRT": "73a4330ef831d38273ef6128bcbff15e4a105421219293ae5454941a3c7301cd",
    "OpenShellEdited.SLDPRT": "c0be437a8c13a50c940b0d9cee51d369865abf3fa0a7ed62610fb9c76eb4b810",
}


def demand(ok, why):
    if not ok:
        raise ValueError(why)


def read_disclosed(directory, name, expected):
    path = directory / name
    demand(path.is_file() and not path.is_symlink(), f"{name} is not the disclosed regular file")
    data = path.read_bytes()
    demand(sha256(data).hexdigest() == expected, f"{name} differs from its native source lock")
    return data


def worker(mode, source, case, transport):
    size = int.from_bytes(transport[:8], "little")
    raw, metadata = transport[8 : 8 + size], loads(transport[8 + size :])
    demand(sha256(raw).hexdigest() == CASES[case], "source custody changed in transport")
    sys.path[:0] = [str(source), str(HERE.parent), str(HERE.parent.parent)]
    from CheckScopedPlainWriter import WriterAudit

    if mode == "archive":
        from ReadShellSidecars import read_shell_save

        import_module("interchange.brep.Validation.BrepValidate")
    else:
        from ReplayShellKernel import read_kernel
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)
    audit = WriterAudit(source, HERE.parent / "NoPublication.SLDPRT")
    sys.addaudithook(audit.observe)
    audit.phase = "cold"
    report = read_shell_save(raw) if mode == "archive" else read_kernel(raw, metadata)
    demand(not audit.denied and not audit.target_opens, "rollback research used external data after setup")
    audit.phase = "done"
    return report | {"post_import_data_accesses": 0}


def library_from_pin(checkout):
    result = run(("git", "archive", KERNEL_PIN, "src"), cwd=ROOT, capture_output=True, check=True, timeout=90)
    with open_tar(fileobj=BytesIO(result.stdout)) as archive:
        archive.extractall(checkout, filter="data")
    return checkout / "src"


def read_in_process(mode, source, case, raw, metadata=None):
    result = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode, "--source", str(source), "--case", case),
        cwd=ROOT, input=len(raw).to_bytes(8, "little") + raw + dumps(metadata).encode(),
        capture_output=True, timeout=60, check=False,
    )
    demand(result.returncode == 0 and not result.stderr, result.stderr.decode())
    return loads(result.stdout)


def measure(directory):
    demand(directory.name == "Disclosure", "supply the named disclosed folder")
    read_disclosed(directory, "Receipt.json", RECEIPT)
    result = run(("git", "diff", "--quiet", ARCHIVE_PIN, "--", "src"), cwd=ROOT, check=False)
    demand(result.returncode == 0, "archive production sources differ from their evidenced starting revision")
    with TemporaryDirectory(prefix="KitPinnedShellKernel.") as scratch:
        kernel = library_from_pin(Path(scratch))
        rows = {}
        for case, digest in CASES.items():
            raw = read_disclosed(directory, case, digest)
            linked = read_in_process("archive", ROOT / "src", case, raw)
            history = read_in_process("kernel", kernel, case, raw, linked)
            demand(read_disclosed(directory, case, digest) == raw, "source changed during paired inspection")
            rows[case] = {"source_sha256": digest, "archive": linked, "rollback": history}
    return {
        "schema": "kit-sw2026-saved-shell-rollback-v1",
        "native_build": "34.5.2.0604", "source_lock_sha256": RECEIPT,
        "archive_codec_revision": ARCHIVE_PIN, "kernel_codec_revision": KERNEL_PIN,
        "fresh_guarded_workers": 4, "native_publications": 0, "private_sources_read": 0, "heldout_credit": 0,
        "cases": rows,
    }


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--disclosure", type=Path)
    modes.add_argument("--worker", choices=("archive", "kernel"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--case", choices=tuple(CASES))
    args = parser.parse_args()
    if args.worker:
        demand(args.source is not None and args.case is not None, "missing bounded worker inputs")
        print(dumps(worker(args.worker, args.source, args.case, sys.stdin.buffer.read()), sort_keys=True, allow_nan=False))
        return
    demand(args.output is not None, "choose a fresh output path")
    report = measure(args.disclosure.resolve(strict=True))
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
