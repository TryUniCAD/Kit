from argparse import ArgumentParser
from hashlib import sha256
import json
from math import pi
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.DimensionFields import KDimensionFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import KResolvedLayouts
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut import ReadFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadSchemaMut import ReadSchemaMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader

from PatternAngleArc import make_angle_arc_fields
from PatternHingeGeometry import derive_hinge


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def serialize_arc(rules, fields):
    context = BodyContext(19000, KResolvedLayouts, {}, {})
    writer = BodyWriter(ArchiveMaps(1), context, WriteBodyMut)
    owner = ArchiveNode(RuntimeClass("moDisplayAngularDim_c", 1), fields)
    WriteFieldsMut(WriteFrame(writer, FieldScope(fields), owner, WriteSchemaMut, WriteFieldsMut), rules)
    require(writer.MapValue.CounterValue == 1, "standalone arc fields allocated a graph node")
    return bytes(writer.OutputValue)


def read_arc(rules, raw):
    context = BodyContext(19000, KResolvedLayouts, {}, {})
    cursor = BinaryReader(raw)
    reader = GraphReader(cursor, ArchiveMaps(1), ReadBodyMut)
    fields = {}
    owner = ArchiveNode(RuntimeClass("moDisplayAngularDim_c", 1), fields)
    ReadFieldsMut(ReadFrame(context, reader, FieldScope(fields), owner, ReadSchemaMut, ReadFieldsMut), rules)
    require(cursor.GetRemaining() == 0 and reader.MapValue.CounterValue == 1,
            "arc field reader changed its exact standalone field boundary")
    return fields


def model_refusals(ends, angle, shallow_ends):
    probes = (
        ("swapped_finite_hinge", tuple(reversed(ends)), angle, False, "actual directed through-origin"),
        ("reverse_constraint", ends, angle, True, "acute unreversed"),
        ("straight_angle", ends, pi, False, "acute unreversed"),
        ("parallel_tolerance", ends, 1e-5, False, "different centre branch"),
        ("interior_label", shallow_ends, pi / 6.0, False, "exterior to the first witness"),
    )
    rejected = {}
    for role, endpoints, supplied, reverse, expected in probes:
        try:
            make_angle_arc_fields(*endpoints, supplied, reverse=reverse)
        except ValueError as error:
            require(expected in str(error), "unexpected refusal for " + role)
            rejected[role] = str(error)
    require(len(rejected) == len(probes), "an unproved arc state passed the scoped composer")
    return rejected


def main():
    ArgumentParser().parse_args()
    request = json.load(sys.stdin)
    audit.BeginBuild()
    require(type(request) is dict and set(request) == {"plate_box_m", "raised_box_m", "angle_rad", "reverse"},
            "angular arc accepts only independent neutral stock and angle intent")
    ends = derive_hinge(request["plate_box_m"], request["raised_box_m"])["ordered_endpoints_m"]
    tiny = derive_hinge(((0.0, 0.0, 0.0), (0.07, 0.08, 0.0002)),
                       ((0.01, 0.02, 0.0), (0.03, 0.04, 0.0006)))["ordered_endpoints_m"]
    fields = make_angle_arc_fields(*ends, request["angle_rad"], reverse=request["reverse"])
    rules = tuple(rule for schema in ("moDisplayDim_c.FUN_4c82c3d0", "moDisplayArcDim_c.FUN_4c82b8f0")
                  for rule in KDimensionFields[schema] if rule.NameValue in fields)
    require(tuple(rule.NameValue for rule in rules) == tuple(fields),
            "arc fields no longer follow the shared typed serializer order")
    raw = serialize_arc(rules, fields)
    decoded = read_arc(rules, raw)
    require(decoded == fields and serialize_arc(rules, decoded) == raw, "generated typed arc field slice did not round-trip")
    result = {"ordered_field_names": list(fields), "selected_endpoints_m": ends, "fields": decoded,
              "field_slice_sha256": sha256(raw).hexdigest(), "field_slice_bytes": len(raw),
              "guarded_runtime_reads": len(audit.DeniedReads), "cad_files_written": 0,
              "refusals": model_refusals(ends, request["angle_rad"], tiny)}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
