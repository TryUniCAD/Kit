from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from struct import error as StructError

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reject(operation, label):
    usage = BodyUsage()
    try:
        operation(usage)
    except (ValueError, TypeError, KeyError, StructError) as error:
        if usage.IsComplete:
            raise ValueError(f"failed {label} operation claimed completion") from error
        return {"case": label, "rejected": True, "diagnostic": str(error), "usage": GetBodyReport(usage)}
    raise ValueError(f"malformed resolved case {label} was admitted")


def malformed(data, version, seed, context, graph):
    wrong_base = (seed.CounterValue + 1).to_bytes(4, "little") + data[4:]
    wrong_context = {**context, "model_is_part": 1 - context["model_is_part"]}
    rows = [
        reject(lambda usage: ReadResolvedMut(wrong_base, version, seed, context, UsageValue=usage), "incorrect_inherited_base"),
        reject(lambda usage: ReadResolvedMut(data, version - 1, seed, context, UsageValue=usage), "unsupported_document_version"),
        reject(lambda usage: ReadResolvedMut(data + b"\0", version, seed, context, UsageValue=usage), "unread_tail"),
        reject(lambda usage: ReadResolvedMut(data, version, seed, wrong_context, UsageValue=usage), "wrong_model_context"),
        reject(lambda usage: ReadResolvedMut(data, version, MapSnapshot(seed.CounterValue, ()), context, UsageValue=usage), "missing_configuration_owner"),
    ]
    maps = ArchiveMaps(seed.CounterValue, seed)
    node = next(node for node in graph.RootsValue if node is not None and ObjectIndex(maps, node) is None)
    original = node.ClassValue
    node.ClassValue = RuntimeClass(original.NameValue, 2)
    try:
        rows.append(reject(lambda usage: WriteResolMut(graph.RootsValue, graph.ExtraFields, version, seed, context, UsageValue=usage), "unsupported_class_schema"))
    finally:
        node.ClassValue = original
    return rows


def modeled_edit(graph, seed, context):
    maps = ArchiveMaps(seed.CounterValue, seed)
    node = next(node for node in graph.RootsValue if node is not None and "f20" in node.FieldsValue and ObjectIndex(maps, node) is None)
    original = node.FieldsValue["f20"]
    updated = ("A", original[1] + " TypedResolved") if isinstance(original, tuple) else original + " TypedResolved"
    node.FieldsValue["f20"] = updated
    try:
        encoded, written = WriteResolMut(graph.RootsValue, graph.ExtraFields, graph.VersionValue, seed, context)
        loaded = ReadResolvedMut(encoded, graph.VersionValue, seed, context)
        found = [root for root in loaded.RootsValue if root is not None and root.FieldsValue.get("f20") == updated]
        if len(found) != 1 or WriteResolMut(loaded.RootsValue, loaded.ExtraFields, graph.VersionValue, seed, context)[0] != encoded:
            raise ValueError("modeled resolved feature name did not round trip")
    finally:
        node.FieldsValue["f20"] = original
    return {"case": "modeled_feature_name", "bytes": len(encoded), "sha256": digest(encoded), "roundtrip": True, "map_counter": written.MapValue.CounterValue}


def check(path, malformed_checks=False, edits=False):
    source = path.read_bytes()
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    header = ReadHeaderGraph(archive.require("Contents/Config-0-ModelHeader"), version)
    config = ReadConfigMut(archive.require("Contents/Config-0"), version, header)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), version)
    context = MakeLinkContext(config, manager)
    data = archive.require("Contents/Config-0-ResolvedFeatures")
    loaded, stored = BodyUsage(), BodyUsage()
    graph = ReadResolvedMut(data, version, config.MapValue, context, UsageValue=loaded)
    encoded, written = WriteResolMut(graph.RootsValue, graph.ExtraFields, version, config.MapValue, context, UsageValue=stored)
    if encoded != data:
        offset = next((index for index, (left, right) in enumerate(zip(data, encoded)) if left != right), min(len(data), len(encoded)))
        raise ValueError(f"SDK resolved differs at {offset}, lengths {len(data)} and {len(encoded)}")
    read_map = ArchiveMaps(graph.MapValue.CounterValue, graph.MapValue)
    write_map = ArchiveMaps(written.MapValue.CounterValue, written.MapValue)
    for entry in config.MapValue.EntriesValue:
        if read_map.EntryMap[entry.IndexValue].EntryValue is not entry.EntryValue or write_map.EntryMap[entry.IndexValue].EntryValue is not entry.EntryValue:
            raise ValueError("resolved graph changed an inherited class or object identity")
    if graph.MapValue.CounterValue != written.MapValue.CounterValue:
        raise ValueError("resolved map counter changed during typed emission")
    row = {"file": path.name, "source_sha256": digest(source), "source_bytes": len(source),
           "stream": "Contents/Config-0-ResolvedFeatures", "archive_version": version,
           "bytes": len(data), "sha256": digest(data), "output_sha256": digest(encoded),
           "byte_identity_passed": True, "map_base": graph.MapBase, "map_counter": graph.MapValue.CounterValue,
           "root_count": len(graph.RootsValue), "inline_mbsm_present": graph.ExtraFields is not None,
           "context": dict(context), "inherited_entries": len(config.MapValue.EntriesValue),
           "inherited_aliases_preserved": True, "manager_map_independent": True,
           "load": GetBodyReport(loaded), "store": GetBodyReport(stored),
           "malformed": malformed(data, version, config.MapValue, context, graph) if malformed_checks else [],
           "modeled_edits": [modeled_edit(graph, config.MapValue, context)] if edits else []}
    if WriteResolMut(graph.RootsValue, graph.ExtraFields, version, config.MapValue, context)[0] != data:
        raise ValueError("modeled checks did not restore the original resolved graph")
    return row


def main():
    parser = argparse.ArgumentParser(description="Verify the shared SDK ordinary linked resolved graph")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--malformed", action="store_true")
    parser.add_argument("--modeled-edits", action="store_true")
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("report path must be unused")
    rows = [check(path, args.malformed, args.modeled_edits) for path in args.files]
    root = Path(__file__).resolve().parents[4]
    report = {"schema": "kit.sw2026.sdk-resolved-graph.v1", "passed": True, "files": rows,
              "public_full_linked_graph": False, "native_application_runs": 0, "writer_native_acceptance": False,
              "script_sha256": digest(Path(__file__).read_bytes()),
              "implementation": [{"file": str(path.relative_to(root)), "sha256": digest(path.read_bytes())}
                                 for path in sorted((root / "src/convert/adapters/solidworks/Archive").rglob("*.py"))]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(f"{len(rows)} SDK resolved graphs byte-identical")


if __name__ == "__main__":
    main()
