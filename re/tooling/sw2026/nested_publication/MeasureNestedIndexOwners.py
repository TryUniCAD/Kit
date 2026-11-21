from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
from tempfile import TemporaryDirectory
import json
import sys
import tarfile

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from MeasureNestedReadback import FrozenReads, checked, digest, require


BASE = "42878d802e4d53ba1dd92528a67fa8122880cff0"
GENERATED = ("SdkNestedNeutralNative01.json", "aa786c6aa4bc7bdae15662c4b4908205b7a0fda7fdb5bb1bb503594a6b0fb967")
ORIGINAL = "NestedAssemblyDisclosedReplayNative01.json"
CHANGES = (
    "src/convert/adapters/solidworks/Assembly/NestedIndex",
    "src/convert/adapters/solidworks/Core/Adapter.py",
)


def git(*args):
    return check_output(("git", "-C", str(ROOT), *args))


def probes(archive, index, child_bytes):
    from convert.adapters.solidworks.Assembly.NestedIndex.ReadNestedIndex import ReadNestedIndex

    identity, *rest = child_bytes
    other = rest[0]
    pairs = index.occurrences
    first = pairs[0]
    cases = (
        ("absent child", index, {key: value for key, value in child_bytes.items() if key != identity}),
        ("different physical child", index, {**child_bytes, identity: child_bytes[other]}),
        ("unresolved configuration", replace(index, occurrences=(replace(first, configuration_name="Other"), *pairs[1:])), child_bytes),
        ("different feature identity", replace(index, occurrences=(replace(first, feature_id=1 << 27), *pairs[1:])), child_bytes),
        ("different local placement", replace(index, occurrences=(replace(first, transform=(*first.transform[:12], first.transform[12] + 0.01, *first.transform[13:])), *pairs[1:])), child_bytes),
    )
    for name, graph, data in cases:
        try:
            ReadNestedIndex(archive, graph, data)
        except (ValueError, TypeError, KeyError):
            continue
        raise ValueError(f"unexpected ownership evidence for {name}")
    return tuple(name for name, _, _ in cases)


def worker(job):
    source = Path(job["source"])
    sys.path.insert(0, str(source / "src"))
    from convert import open_document, write_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks import SldprtAdapter
    from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from interchange.serialization.EncodeData import ToData

    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    require(Path(sys.modules["convert"].__file__).is_relative_to(source / "src"), "unexpected SDK source origin")
    folder = Path(job["folder"])
    paths = {folder / name: pin for name, pin in job["files"].items()}
    path = folder / job["target"]
    guard = FrozenReads(paths)
    guard.code = (source / "src", *guard.code)
    sys.addaudithook(guard.inspect)
    original = {entry.name: checked(entry, pin) for entry, pin in paths.items()}
    report = {}
    for mode in ("resolved", "deferred"):
        document = (open_document(path) if mode == "resolved" else
                    SldprtAdapter().read(path, ReadOptions(values={"resolve_components": False})))
        document.assert_valid()
        require(document.source.sha256 == paths[path] and document.assembly is not None, "unexpected default document")
        wire = ToData(document)
        if mode == "resolved":
            graph = document.assembly
            names = {row.id: row.name for row in graph.definitions}
            captions = {PureWindowsPath(row.attributes["native_source_path"]).stem: row.name for row in graph.definitions}
            placements = [[names[row.owner_definition_id], row.name, names[row.definition_id], row.order]
                          for row in graph.instances]
            destination = BytesIO()
            try:
                write_document(document, destination, destination_format="solidworks.sldasm")
            except ValueError as error:
                require(str(error).startswith("native-only feature definitions cannot be exported:"),
                        "changed original-source writer refusal")
            else:
                raise ValueError("cold input unexpectedly claimed writer admission")
            require(not destination.getvalue(), "refused original source wrote bytes")
            if job["nested"]:
                for row in wire["assembly"]["definitions"]["$tuple"]:
                    row["name"] = "<physical title>"
                for row in wire["assembly"]["instances"]["$tuple"]:
                    row["order"] = "<local order>"
                wire["metadata"].pop("solidworks_source_semantic_sha256")
            report.update({"captions": captions, "placements": placements})
        report[f"{mode}_comparison_sha256"] = digest(json.dumps(wire, sort_keys=True, allow_nan=False).encode())
    if job["probe"]:
        archive = SldprtArchive.from_bytes(original[path.name])
        index = DecodeNativeAsm(archive)
        children = {row.object_id: original[PureWindowsPath(row.source_path).name] for row in index.definitions
                    if row.object_id != index.root_definition_id}
        report["refused_owner_probes"] = probes(archive, index, children)
    for entry, pin in paths.items():
        checked(entry, pin)
    require(not guard.denied and not any(module in ("pythoncom", "pywintypes", "Swapp") or module.startswith("win32com")
                                        for module in sys.modules), "unexpected data or CAD access attempt")
    return report


def render(source, folder, target, pins, nested, probe):
    job = {"source": str(source), "folder": str(folder), "target": target, "files": pins,
           "nested": nested, "probe": probe}
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(job), text=True,
                 capture_output=True, timeout=120)
    require(result.returncode == 0 and not result.stderr, result.stderr[-4000:])
    return json.loads(result.stdout)


def bundles(workspace):
    measure = ROOT / "re/solidworks/measurements/2026"
    for row in json.loads(checked(measure / GENERATED[0], GENERATED[1]))["cases"]:
        folder = workspace / row["case"]
        fixture = json.loads(checked(folder / "Fixture.json", row["fixture_sha256"]))
        pins = {value["file"]: value["sha256"] for value in fixture["files"].values()}
        yield row["case"], folder / "FrozenGenerated", "SdkFrame.SLDASM", pins
    original_pin = digest(git("show", f"{BASE}:re/solidworks/measurements/2026/{ORIGINAL}"))
    for case, pin in json.loads(checked(measure / ORIGINAL, original_pin))["author_record_sha256"].items():
        folder = workspace / "NestedAssemblySource01" / "Results" / case
        record = json.loads(checked(folder / "Author.json", pin))["result"]
        author = folder / "Author"
        pins = {path.name: record["saved_files"][path.stem]["sha256"] for path in author.iterdir()}
        yield case, author, f"{record['restored']['root']}.SLDASM", pins


def audit(workspace):
    changed = set(git("diff", "--name-only", BASE, "--", "src").decode().splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard", "--", "src").decode().splitlines())
    require(changed and all(any(path == prefix or path.startswith(prefix + "/") for prefix in CHANGES)
                            for path in changed), "unexpected SDK source changes")
    source_digests = {path: digest((ROOT / path).read_bytes()) for path in sorted(changed)}
    outcomes = {}
    with TemporaryDirectory(prefix="KitNestedIndex") as folder:
        baseline = Path(folder).resolve()
        with tarfile.open(fileobj=BytesIO(git("archive", BASE, "src"))) as snapshot:
            snapshot.extractall(baseline, filter="data")
        for name, area, root, pins in bundles(workspace):
            require(area.resolve() == area and {item.name for item in area.iterdir()} == set(pins), "unexpected bundle inventory")
            cases = {}
            for target in sorted(name for name in pins if name.upper().endswith(".SLDASM")):
                nested = target == root
                old = render(baseline, area, target, pins, nested, False)
                new = render(ROOT, area, target, pins, nested, nested)
                require(old["resolved_comparison_sha256"] == new["resolved_comparison_sha256"] and
                        old["deferred_comparison_sha256"] == new["deferred_comparison_sha256"],
                        "the SDK altered unrelated document or deferred reader state")
                if nested:
                    expected = {Path(name).stem for name in pins}
                    require(new["captions"] == {label: label for label in expected},
                            "closed component set has an incorrect physical title")
                    orders = {}
                    for owner, _, _, order in new["placements"]:
                        orders.setdefault(owner, []).append(order)
                    require(all(values == list(range(len(values))) for values in orders.values()),
                            "owner order changed or remains global")
                else:
                    require(old == new, "standalone direct assembly changed")
                cases[target] = {"input_sha256": pins[target], "nested_root": nested, "before": old, "after": new}
            outcomes[name] = cases
    require(source_digests == {path: digest((ROOT / path).read_bytes()) for path in sorted(changed)},
            "candidate source changed during the run")
    return {"schema": "kit.sw2026.nested-index-owners.v1", "baseline_revision": BASE,
            "baseline_src_tree": git("rev-parse", f"{BASE}:src").decode().strip(),
            "revised_sources_sha256": source_digests, "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
            "fresh_sdk_processes": 2 * sum(len(cases) for cases in outcomes.values()),
            "native_processes_started": 0, "heldout_inputs_read": 0, "same_format_outputs": 0,
            "projected_fields": ["definition name", "owner-local instance order"], "bundles": outcomes}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        require(args.output and args.workspace, "workspace and output path are required")
        raw = (json.dumps(audit(args.workspace.resolve()), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as stream:
            stream.write(raw)
        print(digest(raw))
