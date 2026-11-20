from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha1
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
from subprocess import run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))

from CheckCfgMaster import CONTROLS, ReadCfgMaster, digest, load_case, read_case, report_node, require, source_path
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

AGGREGATE = "9e0a4b85dd21cdfb7feb50eda94593ef9e9b01f9"
SOURCE_REVISION = "0d9d5941a817100bf8533bcc995f88cac28aa9eb"
AUTOMATION = "22075ee5e77c3db9b56bd8c2bc8c415d6baf237d"
ARCHIVE = "convert.adapters.solidworks.Archive."
SHARED_ABI = (
    "Objects.RuntimeClass", "Objects.ExternalClass", "Objects.ArchiveNode",
    "Maps.MapEntry", "Maps.MapSnapshot",
)
MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigMasterPrefix01.json"
COLUMNS = ("slot", "kind", "class", "schema", "native_index", "class_slot", "start", "end", "header_alias")


def prepare_sources(case, folder):
    automation_path = folder / "automation"
    automation_path.mkdir()
    automation_hashes = {}
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_NO_LAZY_FETCH="1", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    bootstrap = ("git", "--no-replace-objects", "--no-optional-locks", "-C", str(ROOT))
    revision = run((*bootstrap, "rev-parse", "--verify", AUTOMATION + "^{commit}"),
                   capture_output=True, check=True, timeout=20, env=env).stdout.decode().strip()
    for name in ("Corpus.py", "Evidence.py"):
        payload = run((*bootstrap, "show", f"{revision}:re/automation/{name}"), capture_output=True,
                      check=True, timeout=20, env=env).stdout
        (automation_path / name).write_bytes(payload)
        automation_hashes[name] = digest(payload)
    sys.path.insert(0, str(automation_path))
    from Corpus import git, read_tree

    source = source_path(case).relative_to(ROOT).as_posix()
    blob = read_tree(ROOT, SOURCE_REVISION)[source]
    raw = load_case(case)
    require(raw == git(ROOT, "cat-file", "blob", blob), "disclosed source differs from its pinned Git blob")
    entries = read_tree(ROOT, AGGREGATE)
    reference = folder / "reference"
    reference.mkdir()
    with open_tar(fileobj=BytesIO(git(ROOT, "archive", "--format=tar", AGGREGATE, "src"))) as archive:
        archive.extractall(reference, filter="data")
    python_files = {f.relative_to(reference).as_posix(): f for f in (reference / "src").rglob("*.py")}
    expected = {path: oid for path, oid in entries.items() if path.startswith("src/") and path.endswith(".py")}
    require(set(python_files) == set(expected), "reference Python source inventory changed")
    for path, file in python_files.items():
        payload = file.read_bytes()
        actual = sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload, usedforsecurity=False).hexdigest()
        require(actual == expected[path], "reference source Git blob changed")
    abi = {}
    for name in SHARED_ABI:
        path = Path("src") / ((ARCHIVE + name).replace(".", "/") + ".py")
        current = (ROOT / path).read_bytes()
        require((reference / path).read_bytes() == current, "source revisions disagree on a shared map type")
        abi[name] = digest(current)
    return raw, (reference / "src").resolve(), {
        "fixture_blob": blob, "fixture_sha256": digest(raw), "fixture_path": source,
        "aggregate_source_tree": git(ROOT, "rev-parse", f"{AGGREGATE}:src").decode().strip(),
        "shared_map_types": abi, "automation_revision": revision, "automation_tools": automation_hashes,
    }


def trace_config(case, config, header, header_nodes, decode, dispatcher):
    captured = {}
    original = dispatcher.KReadActions

    def scalar(frame, rule):
        if rule.NameValue == "f1014" and frame.NodeValue.ClassValue.NameValue == "moPart_c":
            require(not captured, "duplicate part master selector")
            captured.update(
                start=frame.ReaderValue.Cursor.OffsetValue, before=frame.ReaderValue.MapValue.Snapshot(),
                part=frame.NodeValue, conditions=dict(frame.ContextValue.FlagsValue),
            )
        original["Scalar"](frame, rule)

    def branch(frame, rule):
        original["Branch"](frame, rule)
        if rule.NameValue == "f1014" and frame.NodeValue is captured.get("part"):
            require("end" not in captured, "duplicate part master branch")
            captured.update(
                end=frame.ReaderValue.Cursor.OffsetValue, after=frame.ReaderValue.MapValue.Snapshot(),
                selector=frame.ScopeValue.FieldsValue["f1014"], node=frame.ScopeValue.FieldsValue.get("f1018"),
            )
            captured["result"] = check_bridge(case, config, captured, header_nodes)

    dispatcher.KReadActions = {**original, "Scalar": scalar, "Branch": branch}
    try:
        graph = decode(config, 19000, header)
    finally:
        dispatcher.KReadActions = original
    require(graph.ReportValue["completed"] and not graph.ReportValue["missing_schemas"]
            and not graph.ReportValue["provisional_schemas"] and graph.RootValue is captured.get("part")
            and graph.RootValue.EndOffset == len(config), "aggregate did not consume the original Config-0")
    return captured["result"]


def use_reference(case, reference, config, header_bytes, guard):
    def sdk_module(name):
        return name.split(".", 1)[0] in ("convert", "interchange")

    initial_paths = sys.path[:]
    current_modules = {k: v for k, v in sys.modules.copy().items() if sdk_module(k)}
    require(all(ARCHIVE + name in current_modules for name in SHARED_ABI), "required map types were not loaded")
    for name in current_modules:
        if name not in {ARCHIVE + key for key in SHARED_ABI}:
            del sys.modules[name]
    sys.path.insert(0, str(reference))
    try:
        from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
        from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
        from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
        dispatcher = import_module(ARCHIVE + "Bodies.Reading.ReadFieldsMut")
        origin = Path(sys.modules[ReadConfigMut.__module__].__file__).resolve()
        require(origin.is_relative_to(reference), "unexpected aggregate configuration reader")
        guard["active"] = True
        header = ReadHeaderGraph(header_bytes, 19000)
        return trace_config(case, config, header, HeaderRefNodes(header, 19000), ReadConfigMut, dispatcher)
    finally:
        guard["active"] = False
        sys.path[:] = initial_paths
        for name in list(sys.modules):
            if sdk_module(name):
                del sys.modules[name]
        sys.modules.update(current_modules)


def describe_map(snapshot, header_nodes):
    classes = {id(e.EntryValue): e.IndexValue for e in snapshot.EntriesValue
               if not isinstance(e.EntryValue, ArchiveNode)}
    rows = []
    for entry in snapshot.EntriesValue:
        value = entry.EntryValue
        tagged = isinstance(value, ArchiveNode)
        runtime = value.ClassValue if tagged else value
        rows.append([
            entry.IndexValue, type(value).__name__, runtime.NameValue, getattr(runtime, "SchemaValue", None),
            getattr(value, "IndexValue", None), classes.get(id(runtime)) if tagged else None,
            getattr(value, "StartOffset", None), getattr(value, "EndOffset", None),
            any(value is node for node in header_nodes),
        ])
    return rows


def check_bridge(case, config, captured, header_nodes):
    _, _, _, _, interval, bridge_hash, counter, selector, _ = CONTROLS[case]
    first, final = captured["start"], captured["end"]
    before, after = captured["before"], captured["after"]
    data = config[first:final]
    part = captured["part"]
    require((first, final) == interval and digest(data) == bridge_hash
            and captured["selector"] == selector and not any(captured["conditions"].values()),
            "traversed master boundary or context differs")
    require(before.CounterValue == after.CounterValue == counter
            and [entry.IndexValue for entry in before.EntriesValue] == list(range(1, counter))
            and all(a is b for a, b in zip(before.EntriesValue, after.EntriesValue, strict=True))
            and before.EntriesValue[1].EntryValue is part
            and tuple(e.EntryValue for e in before.EntriesValue if any(e.EntryValue is node for node in header_nodes))
                == header_nodes, "physical prefix map or header identity differs")
    original = captured["node"]
    original_fields = tuple(part.FieldsValue.items())
    result = ReadCfgMaster(data, 19000, before, part)
    require(tuple(part.FieldsValue.items()) == original_fields, "bounded master changed its real part owner")
    require((result is None and original is None)
            or (result is not None and original is not None and result.FieldsValue == original.FieldsValue
                and report_node(result) == report_node(original)), "bounded master differs from full physical owner")
    rows = describe_map(before, header_nodes)
    return {
        "interval": [first, final], "selector": selector, "bridge_sha256": digest(data),
        "before_counter": before.CounterValue, "after_counter": after.CounterValue,
        "full_config_bytes": len(config), "full_config_sha256": digest(config),
        "context": captured["conditions"], "prefix_entries": len(rows),
        "prefix_map": rows, "prefix_map_sha256": digest(json.dumps(rows, separators=(",", ":")).encode()),
        "master_fields_sha256": None if result is None else report_node(result)["fields_sha256"],
    }


def run_case(case, folder):
    raw, reference, identity = prepare_sources(case, folder)
    for encoding in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    guard = {"active": False}

    def guarded(event, args):
        if guard["active"]:
            audit_run(event, args)

    sys.addaudithook(guarded)
    guard["active"] = True
    archive, config, _ = read_case(case, raw)
    header = archive.require("Contents/Config-0-ModelHeader")
    guard["active"] = False
    result = use_reference(case, reference, config, header, guard)
    return result | identity | {"runtime_external_accesses": 0}


def main():
    parser = ArgumentParser(description="Traverse the physical Config-0 to recover the full native master map")
    parser.add_argument("case", choices=tuple(CONTROLS))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_bytes()) if args.verify else None
    if manifest is not None:
        require(all(digest((ROOT / path).read_bytes()) == expected
                    for path, expected in manifest["implementation_sha256"].items()),
                "bounded implementation differs from the pinned replay")
    with TemporaryDirectory(prefix="kit-master-prefix-") as temp:
        result = run_case(args.case, Path(temp))
    if manifest is not None:
        require(manifest["map_columns"] == list(COLUMNS) and result == manifest["controls"][args.case],
                "physical prefix replay differs from the pinned result")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
