from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from struct import error as StructError

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require_rejection(operation, label):
    usage = BodyUsage()
    try:
        operation(usage)
    except (TypeError, ValueError, KeyError, StructError) as error:
        if usage.IsComplete:
            raise ValueError(f"failed {label} operation claimed completion") from error
        return {"case": label, "rejected": True, "diagnostic": str(error), "usage": GetBodyReport(usage)}
    raise ValueError(f"malformed configuration {label} was accepted")


def malformed_cases(data, version, header, graph):
    fields = graph.RootValue.FieldsValue
    class_value = graph.RootValue.ClassValue
    offset = 6 + len(class_value.NameValue.encode("ascii"))
    wrong_length = data[:offset] + (1).to_bytes(4, "little") + data[offset + 4:]
    unknown = data[:6] + b"X" * len(class_value.NameValue) + data[offset:]
    rows = [
        require_rejection(lambda usage: ReadConfigMut(wrong_length, version, header, UsageValue=usage), "incorrect_section_length"),
        require_rejection(lambda usage: ReadConfigMut(unknown, version, header, UsageValue=usage), "unknown_runtime_class"),
        require_rejection(lambda usage: ReadConfigMut(data, version - 1, header, UsageValue=usage), "unsupported_version"),
        require_rejection(lambda usage: ReadConfigMut(data + b"\0", version, header, UsageValue=usage), "unread_tail"),
    ]
    graph.RootValue.ClassValue = ExternalClass(class_value.NameValue, 1)
    try:
        rows.append(require_rejection(lambda usage: WriteConfigMut(graph.RootValue, version, header, UsageValue=usage), "external_class_placeholder"))
    finally:
        graph.RootValue.ClassValue = class_value
    if "f1310" in fields:
        old_value = fields["f1310"]
        fields["f1310"] = [{"key": -1, "value": 0}]
        try:
            rows.append(require_rejection(lambda usage: WriteConfigMut(graph.RootValue, version, header, UsageValue=usage), "unsigned_field_domain"))
        finally:
            fields["f1310"] = old_value
    return rows


def modeled_edits(graph):
    fields = graph.RootValue.FieldsValue
    old_name = fields["f20"]
    new_name = ("A", old_name[1] + " TypedConfig") if isinstance(old_name, tuple) else old_name + " TypedConfig"
    fields["f20"] = new_name
    try:
        encoded, written = WriteConfigMut(graph.RootValue, graph.VersionValue, graph.HeaderValue)
        decoded = ReadConfigMut(encoded, graph.VersionValue, graph.HeaderValue)
        if decoded.RootValue.FieldsValue["f20"] != new_name:
            raise ValueError("modeled configuration name did not survive the real graph codec")
        if WriteConfigMut(decoded.RootValue, decoded.VersionValue, decoded.HeaderValue)[0] != encoded:
            raise ValueError("modeled configuration name did not round trip")
    finally:
        fields["f20"] = old_name
    rows = [{"case": "modeled_name", "changed_bytes": len(encoded), "map_counter": written.MapValue.CounterValue, "roundtrip": True}]
    if "f1310" in fields:
        old_rows = fields["f1310"]
        new_rows = [*old_rows, {"key": 127001, "value": 3}]
        fields["f1310"] = new_rows
        try:
            expanded, written = WriteConfigMut(graph.RootValue, graph.VersionValue, graph.HeaderValue)
            decoded = ReadConfigMut(expanded, graph.VersionValue, graph.HeaderValue)
            output = decoded.RootValue.FieldsValue
            if output["f1310"] != new_rows or output["n1318"] != len(new_rows):
                raise ValueError("modeled array length was not recomputed from its rows")
            if WriteConfigMut(decoded.RootValue, decoded.VersionValue, decoded.HeaderValue)[0] != expanded:
                raise ValueError("modeled array topology did not round trip")
        finally:
            fields["f1310"] = old_rows
        rows.append({"case": "modeled_array_count", "rows_before": len(old_rows), "rows_after": len(new_rows), "changed_bytes": len(expanded), "map_counter": written.MapValue.CounterValue, "roundtrip": True})
    return rows


def check(path, malformed=False, edits=False):
    source = path.read_bytes()
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    data = archive.require("Contents/Config-0")
    header_data = archive.require("Contents/Config-0-ModelHeader")
    header = ReadHeaderGraph(header_data, version)
    direct = HeaderRefNodes(header, version)
    loaded, stored = BodyUsage(), BodyUsage()
    graph = ReadConfigMut(data, version, header, UsageValue=loaded)
    encoded, written = WriteConfigMut(graph.RootValue, version, header, UsageValue=stored)
    if encoded != data:
        offset = next((index for index, (left, right) in enumerate(zip(data, encoded)) if left != right), min(len(data), len(encoded)))
        raise ValueError(f"SDK Config differs at {offset}, lengths {len(data)} and {len(encoded)}")
    maps = ArchiveMaps(graph.MapValue.CounterValue, graph.MapValue)
    write_maps = ArchiveMaps(written.MapValue.CounterValue, written.MapValue)
    aliases = [{"ordinal": index, "class": node.ClassValue.NameValue,
                "index": ObjectIndex(maps, node), "stored_index": ObjectIndex(write_maps, node),
                "same_header_object": maps.EntryMap[ObjectIndex(maps, node)].EntryValue is node}
               for index, node in enumerate(direct)]
    if any(row["index"] != row["stored_index"] or not row["same_header_object"] for row in aliases):
        raise ValueError("configuration direct alias identities were not preserved")
    if graph.MapBase != written.MapBase or graph.MapValue.CounterValue != written.MapValue.CounterValue:
        raise ValueError("configuration map boundaries changed during emission")
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), version)
    context = MakeLinkContext(graph, manager)
    if any(left.EntryValue is right.EntryValue for left in manager.MapValue.EntriesValue for right in graph.MapValue.EntriesValue):
        raise ValueError("independent configuration manager borrowed a configuration map entry")
    row = {
        "file": path.name, "source_sha256": digest(source), "source_bytes": len(source),
        "stream": "Contents/Config-0", "archive_version": version,
        "model_class": graph.RootValue.ClassValue.NameValue,
        "bytes": len(data), "sha256": digest(data), "output_sha256": digest(encoded),
        "byte_identity_passed": True, "map_base": graph.MapBase,
        "map_counter": graph.MapValue.CounterValue,
        "header_sha256": digest(header_data), "header_direct_aliases": aliases,
        "manager_map_base": 1, "manager_map_counter": manager.MapValue.CounterValue,
        "resolved_context": dict(context), "manager_map_independent": True,
        "load": GetBodyReport(loaded), "store": GetBodyReport(stored),
        "malformed": malformed_cases(data, version, header, graph) if malformed else [],
        "modeled_edits": modeled_edits(graph) if edits else [],
    }
    if WriteConfigMut(graph.RootValue, version, header)[0] != data:
        raise ValueError("modeled checks did not restore their original graph")
    return row


def main():
    parser = argparse.ArgumentParser(description="Check the shared SDK ordinary typed Config graph")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--malformed", action="store_true")
    parser.add_argument("--modeled-edits", action="store_true")
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("report path must be unused")
    rows = [check(path, args.malformed, args.modeled_edits) for path in args.files]
    root = Path(__file__).resolve().parents[4]
    report = {
        "schema": "kit.sw2026.sdk-config-graph.v1", "passed": True,
        "files": rows, "public_full_linked_graph": False,
        "resolved_body_codec_promoted": False, "native_application_runs": 0,
        "writer_native_acceptance": False,
        "script_sha256": digest(Path(__file__).read_bytes()),
        "implementation": [{"file": str(path.relative_to(root)), "sha256": digest(path.read_bytes())}
                           for path in sorted((root / "src/convert/adapters/solidworks/Archive").rglob("*.py"))],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(f"{len(rows)} SDK Config graphs byte-identical")


if __name__ == "__main__":
    main()
