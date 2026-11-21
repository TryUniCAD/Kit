from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def class_name(node):
    require(type(node) is ArchiveNode and type(node.ClassValue) is RuntimeClass, "prepared native object is not a concrete archive node")
    return node.ClassValue.NameValue


def wire_index(fields, short_name, long_name, marker, expected):
    short = fields[short_name]
    require(type(short) is int and short == min(expected, marker), "prepared compact index differs from the ordered native target")
    if short == marker:
        require(long_name in fields, "prepared marker index is missing its extended wire field")
        index = fields[long_name]
        require(type(index) is int and marker <= index == expected, "prepared extended index differs from the ordered native target")
    else:
        require(long_name not in fields, "prepared compact index has an unexpected extended wire field")
        index = short
    require(index == expected, "prepared native index differs from the ordered target")
    return index


def check_geometry(sketch, positions):
    fields = sketch.FieldsValue
    points, lines = fields["points"], fields["lines"]
    count = len(positions)
    require(fields["npoints"] == fields["nlines"] == len(points) == len(lines) == count, "prepared ring counts differ from neutral topology")
    require(fields["f130"] == fields["f56c"] == count + 1, "prepared permanent or modification counter differs")
    require(fields["f140"]["f08"] == fields["f140"]["f0c"] == count + 1, "prepared independent creation counters differ")
    require(all(value == 1 for name, value in fields["f140"].items() if name not in ("f08", "f0c", "f40")) and fields["f140"]["f40"] == 0,
            "prepared unused creation counters changed")
    require(fields["f128"] == fields["f12c"] == 1 and fields["f188"] == 0, "prepared constructor solver or local reference state differs")
    handles = []
    encodings = {"compact_handles": 0, "extended_handles": 0, "compact_endpoints": 0, "extended_endpoints": 0}
    for index, (row, position) in enumerate(zip(points, positions, strict=True)):
        point = row["point"]
        require(point["pflags"] == 0x1E and point["dflt"] == 0,
                "prepared point must select ordinary two dimensional position adjacency and status fields")
        require(row["kind"] == 0 and point["pos"] == {"x": position[0], "y": position[1]}, "prepared point position or kind differs")
        require(point["f0c"] == index + 1 and point["f08"] == 0 and point["fe8"] == 2, "prepared point namespaces or degree differ")
        require(point["f30"] == 5 and point["f34"] == 1 and point["pflags"] == 0x1E, "prepared point constructor state differs")
        incident = (0, count - 1) if index == 0 else (index - 1, index)
        for key, expected in zip(("h1", "h2"), incident, strict=True):
            handle = point[key]
            require(class_name(handle) == "sgLineHandle", "prepared adjacency has the wrong runtime class")
            require(wire_index(handle.FieldsValue, "idx", "f18", 0x777F, expected) == expected,
                    "prepared adjacency points to the wrong line index")
            encodings["extended_handles" if handle.FieldsValue["idx"] == 0x777F else "compact_handles"] += 1
            require(handle.FieldsValue["f1c"] == -1 and handle.FieldsValue["f08"] == 0, "prepared line handle constructor state differs")
            handles.append(handle)
    for index, row in enumerate(lines):
        line = row["line"]
        require(row["flags"] == 0 and wire_index(line, "fc8_s", "fc8", 0xFFFF, index) == index
                and wire_index(line, "fcc_s", "fcc", 0xFFFF, (index + 1) % count) == (index + 1) % count,
                "prepared ordered line endpoints differ")
        for key in ("fc8_s", "fcc_s"):
            encodings["extended_endpoints" if line[key] == 0xFFFF else "compact_endpoints"] += 1
        require(line["f0c"] == line["f08"] == index + 1 and line["fd0"] == 1, "prepared line namespaces or contour state differ")
    require(len({id(handle) for handle in handles}) == 2 * count, "prepared endpoint handle identities were merged")
    return {"point_count": count, "line_count": count, "distinct_endpoint_handles": len(handles), "ordered_endpoints": True,
            "positions": True, "creation_counters": True, "permanent_markers": True, "constructor_solver_state": True,
            "index_encodings": encodings}


def main():
    built = REQUEST["build"]
    blob = b64decode(built["blob"], validate=True)
    require(len(blob) == built["bytes"] and sha256(blob).hexdigest() == built["sha256"], "generated artifact custody differs")
    archive = SldprtArchive.from_bytes(blob)
    header = ReadHeaderGraph(archive.require("Contents/Config-0-ModelHeader"), 19000)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    configuration = ReadConfigMut(archive.require("Contents/Config-0"), 19000, header)
    context = MakeLinkContext(configuration, manager)
    resolved = ReadResolvedMut(archive.require("Contents/Config-0-ResolvedFeatures"), 19000, configuration.MapValue, context)
    profiles = tuple(node for node in resolved.RootsValue if node is not None and class_name(node) == "moProfileFeature_c")
    require(len(profiles) == 1, "prepared graph must contain its one actual ordinary profile")
    profile = profiles[0]
    require(profile.FieldsValue["f3dc"] == 0, "prepared polygon must use the unshared profile sketch branch")
    sketch = profile.FieldsValue["pd_f80"]
    require(class_name(sketch) == "sgSketch", "prepared profile does not retain its actual sketch")
    require("f138" not in sketch.FieldsValue and context.get("ctx874", 0) == 0,
            "ordinary linked preparation must not fabricate the context-only sketch backlink")
    plane = profile.FieldsValue["pd_f78"]
    require(class_name(plane) == "moCompRefPlane_c", "prepared profile lost its actual component plane")
    component = plane.FieldsValue["f58"]
    require(class_name(component) == "moUnitComponent_c" and component.FieldsValue["owner"] is configuration.RootValue,
            "prepared profile plane lost its serialized actual model owner")
    extrusions = tuple(node for node in resolved.RootsValue if node is not None and class_name(node) == "moExtrusion_c")
    require(len(extrusions) == 1 and any(row["o"] is profile for row in extrusions[0].FieldsValue["f60"]["list"]["items"]),
            "prepared extrusion lost its actual profile dependency")
    members = {entry.IndexValue: entry.EntryValue for entry in resolved.MapValue.EntriesValue}
    require(all(members[entry.IndexValue] is entry.EntryValue for entry in configuration.MapValue.EntriesValue), "prepared resolved map lost configuration aliases")
    require(all(node.IndexValue is not None and members[node.IndexValue] is node for node in (profile, sketch, plane, component)),
            "prepared profile sketch and plane graph lost their actual archive object identities")
    geometry = check_geometry(sketch, REQUEST["request"]["document"]["vertices_m"])
    encoded, repeated = WriteConfigMut(configuration.RootValue, 19000, header)
    require(repeated.MapValue.CounterValue == configuration.MapValue.CounterValue, "prepared configuration map changed on serialization")
    actual = {"Contents/Config-0": encoded, "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
              "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000),
              "Contents/Config-0-ResolvedFeatures": WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, configuration.MapValue, context)[0],
              "Header2": WriteHeadGraph(ReadHeaderGraph(archive.require("Header2"), 19000), 19000)}
    comparisons = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "byte_identity": data == archive.require(name)} for name, data in actual.items()}
    require(all(row["byte_identity"] for row in comparisons.values()), "separate prepared graph failed SDK byte identity")
    require(all(report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"]
                for report in (manager.ReportValue, configuration.ReportValue, resolved.ReportValue)), "prepared graph used incomplete grammar")
    return {"passed": True, "scope": "separate SDK preparation of independently generated polygon graph",
            "artifact_sha256": sha256(blob).hexdigest(), "geometry": geometry, "streams": comparisons,
            "profile_sketch_alias": True, "runtime_backlink_not_serialized": True,
            "model_owner_alias": True, "extrusion_dependency_alias": True,
            "linked_map_aliases": True, "config_map_counter": configuration.MapValue.CounterValue,
            "resolved_map_counter": resolved.MapValue.CounterValue, "resolved_usage": resolved.ReportValue,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
