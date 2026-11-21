import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def load_sdk(root):
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    return locals()


def graph_digest(snapshot, sdk):
    nodes = sdk["ArchiveNode"]
    classes = (sdk["RuntimeClass"], sdk["ExternalClass"])
    slots = {id(entry.EntryValue): entry.IndexValue for entry in snapshot.EntriesValue}

    def value(item):
        if isinstance(item, nodes):
            if id(item) in slots:
                return ["node", slots[id(item)]]
            return ["owned", value(item.ClassValue), value(item.FieldsValue)]
        if isinstance(item, classes):
            return ["class", item.NameValue, getattr(item, "SchemaValue", None), getattr(item, "IndexValue", None)]
        if is_dataclass(item):
            return ["record", type(item).__name__, {field.name: value(getattr(item, field.name)) for field in fields(item)}]
        if isinstance(item, Mapping):
            return {key: value(data) for key, data in sorted(item.items())}
        if isinstance(item, (tuple, list)):
            return [value(data) for data in item]
        if isinstance(item, float):
            return ["float", item.hex()]
        if isinstance(item, bytes):
            return ["bytes", len(item), digest(item)]
        require(item is None or type(item) in (str, int, bool), "unexpected typed field value")
        return item

    rows = []
    for entry in snapshot.EntriesValue:
        item = entry.EntryValue
        payload = [value(item.ClassValue), value(item.FieldsValue)] if isinstance(item, nodes) else value(item)
        rows.append([entry.IndexValue, payload])
    return digest(json.dumps([snapshot.CounterValue, rows], sort_keys=True, separators=(",", ":")).encode())


def aliases(seed, extended):
    entries = {entry.IndexValue: entry.EntryValue for entry in extended.EntriesValue}
    require(all(entries.get(entry.IndexValue) is entry.EntryValue for entry in seed.EntriesValue), "inherited map identity changed")
    return len(seed.EntriesValue)


def endpoints(graph, resolved, sdk):
    owner = sdk["FindModelRoot"](resolved.MapValue)
    inherited = {id(entry.EntryValue): entry.IndexValue for entry in resolved.MapValue.EntriesValue}
    rows = []
    for mate in graph.RootsValue:
        detached = mate.FieldsValue["f3c8"]
        actual = mate.FieldsValue["f410"]
        require(len(detached) == len(actual) == 2, "ordinary planar endpoint count differs")
        for ordinal, row in enumerate(actual):
            wrapper = row["o"]
            reference = wrapper.FieldsValue["f58"]
            component = reference.FieldsValue["f58"]
            require(component.ClassValue.NameValue == "moChainComponent_c", "resolved endpoint lacks its actual chain component")
            require(component.FieldsValue["owner"] is owner, "endpoint component owner identity differs")
            chain = component.FieldsValue["f20"]
            external = chain.FieldsValue["f08"]
            branch = external.FieldsValue["f08"]
            require(len(branch) == 1, "ordinary endpoint path is not one hop")
            target = branch[0]["o"]
            occurrence = target.FieldsValue["f50"]
            require(id(target) in inherited and id(occurrence) in inherited, "endpoint invented an occurrence or external entry")
            require(occurrence.FieldsValue["f4f8"] is target, "endpoint external entry does not alias the occurrence entry")
            require(wrapper.FieldsValue["f78"] == wrapper.FieldsValue["f7c"] == ordinal, "endpoint ordinal differs")
            require(detached[ordinal]["k"] == ordinal, "detached endpoint ordinal differs")
            rows.append({"ordinal": ordinal, "occurrence_slot": inherited[id(occurrence)], "external_slot": inherited[id(target)], "component_owner_is_model": True, "external_identity_preserved": True})
    return rows


def rejected(name, operation):
    try:
        operation()
    except (ValueError, TypeError, KeyError) as error:
        return {"case": name, "rejected": True, "error_type": type(error).__name__}
    raise ValueError(f"negative unexpectedly accepted: {name}")


def negatives(blob, resolved, graph, sdk):
    read = sdk["ReadMatesMut"]
    write = sdk["WriteMatesMut"]
    node = sdk["ArchiveNode"]
    runtime = sdk["RuntimeClass"]
    snapshot = sdk["MapSnapshot"]
    count = resolved.MapValue.CounterValue
    prefix = count.to_bytes(4, "little", signed=True)
    negatives = [
        rejected("counter_only_context", lambda: read(blob, count)),
        rejected("unsupported_version", lambda: read(blob, replace(resolved, VersionValue=19001))),
        rejected("wrong_inherited_counter", lambda: read((count + 1).to_bytes(4, "little") + blob[4:], resolved)),
        rejected("negative_prefix", lambda: read((-1).to_bytes(4, "little", signed=True) + blob[4:], resolved)),
        rejected("trailing_byte", lambda: read(blob + b"\x00", resolved)),
        rejected("truncated_graph", lambda: read(blob[:-1], resolved)),
        rejected("truncated_prefix", lambda: read(blob[:3], resolved)),
        rejected("null_root", lambda: read(prefix + b"\x01\x00\x00\x00", resolved)),
        rejected("null_write_root", lambda: write((None,), resolved)),
        rejected("unrelated_write_root", lambda: write((sdk["FindModelRoot"](resolved.MapValue),), resolved)),
        rejected("unsupported_mate_schema", lambda: write((node(runtime(graph.RootsValue[0].ClassValue.NameValue, 2), dict(graph.RootsValue[0].FieldsValue)),), resolved)),
        rejected("missing_owner_seed", lambda: read(blob, replace(resolved, MapValue=snapshot(count, ())))),
    ]
    endpoint = graph.RootsValue[0].FieldsValue["f410"][0]["o"]
    target = endpoint.FieldsValue["f58"].FieldsValue["f58"].FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"]
    reduced = snapshot(count, tuple(entry for entry in resolved.MapValue.EntriesValue if entry.EntryValue is not target))
    negatives.append(rejected("missing_actual_external_alias", lambda: read(blob, replace(resolved, MapValue=reduced))))
    fields = dict(graph.RootsValue[0].FieldsValue)
    source = fields["f410"][0]["o"]
    changed = node(source.ClassValue, {**source.FieldsValue, "f58": sdk["FindModelRoot"](resolved.MapValue)})
    fields["f410"] = [{"o": changed}, fields["f410"][1]]
    negatives.append(rejected("nonplane_wrapper_reference", lambda: write((node(graph.RootsValue[0].ClassValue, fields),), resolved)))
    return negatives


def worker(root, request):
    sdk = load_sdk(root)
    path = Path(request["path"])
    data = path.read_bytes()
    require(digest(data) == request["sha256"] and len(data) == request["bytes"], "declared assembly identity differs")
    archive = sdk["SldprtArchive"].from_bytes(data)
    link = sdk["ReadNativeLink"](archive, 0)
    resolved = link.ResolvedValue
    blob = archive.require("Contents/Config-0-MatesList")
    require(digest(blob) == request["stream_sha256"], "declared linked stream identity differs")
    initial = graph_digest(resolved.MapValue, sdk)
    graph = sdk["ReadMatesMut"](blob, resolved)
    encoded, stored = sdk["WriteMatesMut"](graph.RootsValue, resolved)
    require(encoded == blob, "mate stream read write identity differs")
    again = sdk["ReadMatesMut"](encoded, resolved)
    require(graph_digest(graph.MapValue, sdk) == graph_digest(again.MapValue, sdk), "typed graph readback differs")
    rows = endpoints(graph, resolved, sdk)
    empty = resolved.MapValue.CounterValue.to_bytes(4, "little", signed=True) + b"\x00\x00"
    empty_graph = sdk["ReadMatesMut"](empty, resolved)
    empty_bytes, empty_stored = sdk["WriteMatesMut"]((), resolved)
    require(empty_bytes == empty and not empty_graph.RootsValue and not empty_stored.RootsValue, "empty list framing differs")
    require(empty_stored.MapValue.CounterValue == resolved.MapValue.CounterValue, "empty list allocated a map slot")
    failures = negatives(blob, resolved, graph, sdk)
    require(graph_digest(resolved.MapValue, sdk) == initial, "mate operations mutated inherited resolved objects")
    require(digest(path.read_bytes()) == request["sha256"], "input changed during proof")
    for value in (graph, stored, again, empty_graph, empty_stored):
        require(value.ReportValue["completed"] and not value.ReportValue["missing_schemas"] and not value.ReportValue["provisional_schemas"], "codec evidence is incomplete")
        for field in value.ReportValue["native_byte_fields"]:
            require(field["completed"] and field["schema"] == "dm.FUN_4bd03960" and field["element_type"] == "f64" and field["declared_length"] == field["observed_length"] == field["element_count"] * 8, "unclassified native byte field")
    return {
        "file_sha256": request["sha256"], "file_bytes": len(data),
        "stream_sha256": digest(blob), "stream_bytes": len(blob),
        "map_base": graph.MapBase, "map_terminal": graph.MapValue.CounterValue,
        "mate_count": len(graph.RootsValue), "mate_classes": [value.ClassValue.NameValue for value in graph.RootsValue],
        "byte_identity": True, "typed_readback_identity": True,
        "inherited_map_aliases": aliases(resolved.MapValue, graph.MapValue),
        "write_inherited_map_aliases": aliases(resolved.MapValue, stored.MapValue),
        "readback_inherited_map_aliases": aliases(resolved.MapValue, again.MapValue),
        "resolved_objects_unchanged": True, "endpoint_aliases": rows,
        "empty_stream_bytes": len(empty), "empty_no_allocation": True,
        "usage": {"read": dict(graph.ReportValue), "write": dict(stored.ReportValue)},
        "negatives": failures, "pid": os.getpid(), "passed": True,
    }


def source_manifest(root):
    files = {}
    for path in sorted((root / "src").rglob("*.py")):
        files[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    tool = Path(__file__).resolve()
    files["re/tooling/sw2026/SdkMatesProcess.py"] = digest(tool.read_bytes())
    return files


def batch(arguments):
    root = arguments.root.resolve()
    source_output = arguments.output.with_suffix(".SourceManifest.json")
    require(not arguments.output.exists() and not source_output.exists(), "integration proof requires unused output paths")
    manifest_data = arguments.cohort.read_bytes()
    linked_data = arguments.linked_proof.read_bytes()
    declared = json.loads(manifest_data)
    linked = json.loads(linked_data)
    require(linked["passed"] and linked["stream_count"] == 6, "linked disclosed custody is not qualified")
    expected = {row["file_sha256"]: row for row in linked["files"]}
    files = [row for row in declared["files"] if Path(row["path"]).suffix.upper() == ".SLDASM"]
    require(len(files) == 6 and {row["sha256"] for row in files} == set(expected), "declared six assembly cohort differs")
    code = source_manifest(root)
    reports = []
    for row in files:
        request = {**row, "stream_sha256": expected[row["sha256"]]["stream_sha256"]}
        result = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--worker", "--root", str(root)], input=json.dumps(request), text=True, capture_output=True, timeout=90, check=False)
        require(result.returncode == 0, f"isolated mate process failed: {result.stderr[-1800:]}")
        report = json.loads(result.stdout)
        old = expected[row["sha256"]]
        require(all(report[key] == old[key] for key in ("stream_bytes", "map_base", "map_terminal", "mate_count", "byte_identity")), "independent linked stream comparison differs")
        reports.append(report)
    require(source_manifest(root) == code, "source closure changed during integration proof")
    require(len({report["pid"] for report in reports}) == 6, "native file proofs did not use six independent processes")
    source_bytes = (json.dumps({"schema": "solidworks-sdk-mates-source-manifest-v1", "files": code}, indent=2, sort_keys=True) + "\n").encode()
    result = {
        "schema": "solidworks-2026-sdk-mates-linked-process-proof-v1",
        "scope": "ordinary version-19000 empty and disclosed two-principal-plane coincident parallel positive-distance codec only",
        "task_id": "B04-SW2026-MATESLIST-CODEC", "delivery_pr": 121,
        "cohort_manifest_sha256": digest(manifest_data), "prior_linked_proof_sha256": digest(linked_data),
        "source_manifest_sha256": digest(source_bytes),
        "source_python_files": len(code), "tool_sha256": digest(Path(__file__).read_bytes()),
        "archive_version": 19000, "container_version": 4,
        "process_count": len(reports), "cases": reports, "passed": True,
        "heldout_inputs_read": False, "native_processes_started": 0,
        "writer_output_count": 0, "public_dispatch_changed": False,
        "native_acceptance_claim": False, "full_family_coverage": False,
        "limitations": ["not a semantic adapter integration", "not a generated native writer trial", "only disclosed inputs", "nonplane and additional mate families remain unsupported"],
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    source_output.write_bytes(source_bytes)
    arguments.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "cases": 6, "output_sha256": digest(arguments.output.read_bytes()), "tool_sha256": result["tool_sha256"]}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--cohort", type=Path)
    parser.add_argument("--linked-proof", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.worker:
        print(json.dumps(worker(arguments.root.resolve(), json.load(sys.stdin)), sort_keys=True))
    else:
        require(all((arguments.cohort, arguments.linked_proof, arguments.output)), "batch requires cohort linked proof and output")
        batch(arguments)


if __name__ == "__main__":
    main()
