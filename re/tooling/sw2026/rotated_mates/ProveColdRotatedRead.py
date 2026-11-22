from argparse import ArgumentParser
from importlib import import_module
from json import dumps, load, loads
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "planar_registry")]
from ProbeColdRotatedSuite import check_public, compile_bundle, stage_bundle
from ProvePlanarMateGroup import controls
from RotatedReadAudit import ROOT, SCOPE, source_only
from VerifyRotatedMates import (
    CHILD,
    FORMAT,
    NATIVE_RECORD,
    PARENT,
    RECEIPT_SHA,
    bad_graph,
    bind,
    finger,
    load_bound,
    paired_inputs,
    read_bound,
    refuse,
    require,
)

BASE = "0bcfe89aa42771224ea01eb4663c1ed11fc7fad7"


def known_pairs(packet, receipt):
    sources = (
        ("original", "Native/A22CombinedRotated/author", "source", "native"),
        ("edited", "WorkingT01", "native", "saved"),
    )
    pairs = [
        {
            "case": label,
            "parent": str(packet / folder / PARENT),
            "child": str(packet / folder / CHILD),
            "parent_sha256": receipt[section][f"{kind}_parent_sha256"],
            "child_sha256": receipt[section][f"{kind}_child_sha256"],
        }
        for label, folder, section, kind in sources
    ]
    return pairs + controls(packet.parent)


def compare_controls(root, rows):
    from convert import open_document

    results = {}
    schema = root / "src/convert/adapters/solidworks/Config/RootLayout.json"
    for row in rows:
        parent, child = Path(row["parent"]), Path(row["child"])
        for role, file in (("parent", parent), ("child", child)):
            read_bound(file, row[f"{role}_sha256"])
        modes = {}
        for mode, geometry in (("full", True), ("design", False)):
            try:
                with source_only((parent, child), (schema,)) as opens:
                    document = open_document(
                        parent, source_format=FORMAT, strict=True, include_brep=geometry
                    )
            except ValueError as error:
                modes[mode] = {"refusal": str(error), "file_opens": dict(opens)}
                continue
            report = document.metadata.get("solidworks.typed_mates_semantics", {})
            require(report.get("scope") != SCOPE, "the new cold route absorbed a previous control")
            modes[mode] = {
                "sha256": finger(document.to_json(indent=None).encode())["sha256"],
                "scope": report.get("scope"),
                "status": report.get("status"),
                "owned_picks": len(document.assembly.mate_entities),
                "parameters": len(document.parameters),
                "file_opens": dict(opens),
            }
        results[row["case"]] = modes
    return results


def check_malformed(root, folder, bundle, members):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

    parent, child = members
    schema = root / "src/convert/adapters/solidworks/Config/RootLayout.json"
    contrast = SldprtArchive.from_bytes(child)
    extra_child = BuildSldprt(
        contrast.streams | {"docProps/ArchiveContrast": b"x"}, FormatVersion=4
    )
    faults = (
        ("UnexpectedOptions", (bad_graph(parent), child), "unsupported auxiliary options"),
        ("UnknownChildRole", (parent, extra_child), "requires an ordinary cold child archive"),
    )
    for stage, inputs, expected in faults:
        paths = stage_bundle(folder / stage, bundle, inputs)
        with source_only(paths, (schema,)):
            refuse(
                lambda: open_document(
                    paths[0], source_format=FORMAT, strict=True, include_brep=False
                ),
                expected,
            )
    missing = folder / "MissingLinkedPart"
    missing.mkdir()
    parent_path = missing / PARENT
    with parent_path.open("xb") as stream:
        stream.write(parent)
    expected = "requires its actual linked part"
    with source_only((parent_path,), (schema,)):
        refuse(
            lambda: open_document(
                parent_path, source_format=FORMAT, strict=True, include_brep=False
            ),
            expected,
        )
    return {**{name: reason for name, _, reason in faults}, "MissingLinkedPart": expected}


def read_cold(root, packet, receipt, bundle):
    parent = packet / "FrozenGeneratedT01" / PARENT
    paths = parent, parent.with_name(CHILD)
    members = tuple(
        read_bound(path, receipt["generation"][f"{role}_sha256"])
        for role, path in zip(("parent", "child"), paths, strict=True)
    )
    with TemporaryDirectory(prefix="KitAggregateRotated-") as directory:
        folder = Path(directory).resolve()
        distance = check_public(
            bundle, paths, members, destination=folder / "NeverPublished" / PARENT
        )
        malformed = check_malformed(root, folder, bundle, members)
    return {
        "scope": SCOPE,
        "linked_child_construction_data_reads": 0,
        "fixed_flags": [True, False],
        "owned_datum_endpoints": 6,
        "strict_modes": 2,
        "relative_linked_reads": 1,
        "deferred_modes": 1,
        "mate_driver_mm": distance,
        "exact_input_files": {
            path.name: finger(raw) for path, raw in zip(paths, members, strict=True)
        },
        "malformed": malformed,
        "public_writer_qualified": False,
    }


def worker(root, job, baseline):
    bind(root)
    import_module("convert")
    control = compare_controls(root, job["controls"])
    if baseline:
        return {"controls": control}
    packet = Path(job["packet"])
    cold = read_cold(root, packet, job["receipt"], job["bundle"])
    generated = tuple(finger(raw) for raw in compile_bundle(job["bundle"]))
    require(
        generated == tuple(cold["exact_input_files"].values()),
        "the current shared serializers did not reproduce the native-measured pair",
    )
    return {"controls": control, "cold": cold, "guarded_generated_files": generated}


def supervise(packet, output):
    receipt = load_bound(ROOT / NATIVE_RECORD, RECEIPT_SHA)
    authored, _ = paired_inputs(packet, receipt)
    job = {
        "packet": str(packet.resolve()),
        "receipt": receipt,
        "bundle": authored["bundle"],
        "controls": known_pairs(packet, receipt),
    }

    def launch(root, baseline=False):
        command = [sys.executable, "-I", "-B", str(HERE), "--worker", "--code-root", str(root)]
        if baseline:
            command.append("--baseline")
        process = run(
            command,
            input=dumps(job),
            encoding="utf-8",
            capture_output=True,
            timeout=90,
            check=False,
        )
        require(process.returncode == 0 and not process.stderr, process.stderr)
        return loads(process.stdout)

    with TemporaryDirectory(prefix="KitAggregateMateBaseline-") as directory:
        archive = check_output(["git", "archive", BASE, "src"], cwd=ROOT)
        extracted = run(
            ["tar", "-x", "-C", directory],
            input=archive,
            capture_output=True,
            check=False,
            timeout=90,
        )
        require(
            extracted.returncode == 0 and not extracted.stderr,
            "unable to prepare aggregate baseline",
        )
        old = launch(Path(directory), baseline=True)
    first, second = launch(ROOT), launch(ROOT)
    require(
        first == second and first["controls"] == old["controls"],
        "cold read was unstable or changed a wider prior reader outcome",
    )
    edits = set()
    for command in (
        ["diff", "--name-only", "-z", BASE, "--", "src"],
        ["ls-files", "--others", "--exclude-standard", "-z", "--", "src"],
    ):
        edits.update(check_output(["git", *command], cwd=ROOT).decode().split("\0"))
    evidence = {
        **first,
        "schema": "kit.sw2026.aggregate-cold-rotated-mates.v1",
        "prior_reader": BASE,
        "native_receipt_sha256": RECEIPT_SHA,
        "native_processes_started": 0,
        "protected_inputs_read": 0,
        "current_workers": 2,
        "baseline_workers": 1,
        "method_sha256": finger(HERE.read_bytes())["sha256"],
        "tool_sha256": {
            path.name: finger(path.read_bytes())["sha256"]
            for path in sorted(HERE.parent.glob("*.py"))
        },
        "source_sha256": {
            name: finger((ROOT / name).read_bytes())["sha256"] for name in sorted(edits - {""})
        },
    }
    with output.open("x", encoding="utf-8") as stream:
        stream.write(dumps(evidence, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(finger(output.read_bytes())["sha256"])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--code-root", type=Path, default=ROOT)
    options = parser.parse_args()
    if options.worker:
        print(dumps(worker(options.code_root, load(sys.stdin), options.baseline), sort_keys=True))
    else:
        supervise(options.disclosed, options.output)
