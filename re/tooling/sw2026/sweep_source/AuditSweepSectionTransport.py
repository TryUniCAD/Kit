from argparse import ArgumentParser
from dataclasses import replace
from math import pi, tau
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE)]

import SweepArchiveLayout
from AuditSweepArchive import check_sdk, digest, guard_runtime, inspect, load_disclosed
from SweepArchiveLayout import section_transport
from SweepArchiveOwners import transport
from SweepModel import require
from SweepSectionTransport import encode_section_nodes, make_section, wrap_section
from convert.Geometry.Parasolid import DecodePartData, EncodeBrepModel, ParaHeaderData, ReadBrepResult
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepBody, BrepCoedge, BrepEdge, BrepFace, BrepFaceUse, BrepLoop, BrepRegion, BrepShell, BrepShellUse, BrepVertex,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector

RADII = (0.003773, 0.005159)


def compare_disclosed(capture):
    cases, lock, _ = load_disclosed(capture)
    observations = []

    def compare_outer(cursor):
        measured = section_transport(cursor)
        lo, hi = measured["span"]
        stored_frame = cursor.BytesValue[lo:hi]
        stored_transmit, = DecodePartData(stored_frame[6:], "native section comparison")
        nodes = tuple(XmtNode(node.index, node.kind, node.fields) for node in measured["nodes"])
        rebuilt = encode_section_nodes(nodes)
        rebuilt_frame = wrap_section(rebuilt)
        require(rebuilt == stored_transmit.data and rebuilt_frame[6:] == stored_frame[6:]
                and rebuilt_frame == stored_frame, "known typed section bytes did not reproduce")
        body = nodes[0]
        require(body.KindValue == 12 and body.Integer("next") not in {node.IndexValue for node in nodes},
                "section native next pointer is not the measured nonresident sibling")
        public_model, public_diagnostic = ReadBrepResult(rebuilt)
        require(public_model is None, "standalone SDK boundary for saved section changed")
        observations.append({
            "raw_sha256": digest(rebuilt), "raw_bytes": len(rebuilt),
            "compressed_wrapper_bytes": len(rebuilt_frame) - 6, "outer_sha256": digest(rebuilt_frame),
            "outer_bytes": len(rebuilt_frame), "stored_next": body.Integer("next"),
            "stored_highest_node_id": body.Integer("highest_node_id"),
            "standalone_brep_diagnostic": public_diagnostic,
            "raw_exact": True, "compressed_wrapper_exact": True, "outer_extent_exact": True,
        })
        return measured

    blocked = guard_runtime()
    SweepArchiveLayout.section_transport = compare_outer
    try:
        for slot, role, raw, phase in cases:
            before = len(observations)
            inspect(slot, role, raw, phase)
            require(len(observations) == before + 1, "saved case lacks one actual section")
            observations[-1].update(slot=slot + 1, role=role, part_sha256=digest(raw))
    finally:
        SweepArchiveLayout.section_transport = section_transport
    require(not blocked, "section retention used external input")
    return {"mode": "disclosed section comparison", "completed": len(observations),
            "source_revision": lock["source_revision"], "observations": observations,
            "blocked_runtime_calls": len(blocked), "generated_part_count": 0}


def historical_model(radius_metres, frame):
    radius_mm = radius_metres * 1000
    circle = CircleCurve("circle", frame.origin, frame.z_axis, frame.x_axis, radius_mm)
    plane = PlaneSurface("plane", frame.origin, frame.z_axis, frame.x_axis)
    seam = BrepVertex("seam", SpaceVector(0.0, 0.0, -radius_mm))
    edge = BrepEdge("rim", seam.id, seam.id, circle.id, 0.0, tau)
    return BrepModel(
        curves=(circle,), surfaces=(plane,), vertices=(seam,), edges=(edge,),
        coedges=(BrepCoedge("use", edge.id),), loops=(BrepLoop("ring", ("use",), outer=True),),
        faces=(BrepFace("face", plane.id, ("ring",)),), face_uses=(BrepFaceUse("face-use", "face"),),
        shells=(BrepShell("sheet", ("face-use",), closed=False),),
        shell_uses=(BrepShellUse("sheet-use", "sheet"),),
        regions=(BrepRegion("region", ("sheet-use",), solid=False),),
        bodies=(BrepBody("body", ("region",)),),
    )


def compare_historical(radius, frame):
    model = historical_model(radius, frame)
    raw = EncodeBrepModel(model, PartValue=False)
    restored, why = ReadBrepResult(raw)
    require(not why and restored is not None and len(restored.faces) == len(restored.vertices) == 1
            and not restored.regions[0].solid and restored.curves[0].radius == radius * 1000,
            "generic sheet control lost a semantic owner")
    vertexless = replace(model, vertices=(), edges=(BrepEdge("rim", "", "", "circle", 0.0, tau),))
    refusals = vertexless.validate()
    require(refusals == ("B-rep edge rim references a missing start vertex",
                         "B-rep edge rim references a missing end vertex"), "generic vertexless guard changed")
    header = ParaHeaderData(raw)
    require(header.schema == "SCH_1200000_12006", "generic sheet route changed its archival schema")
    return {"schema": header.schema, "raw_sha256": digest(raw), "raw_bytes": len(raw),
            "retained_seam_vertices": len(restored.vertices), "vertexless_refusals": list(refusals)}


def compare_model():
    basis = PrincipalFrame("x")
    frame = Transform(*(SpaceVector(*row) for row in (basis.OriginValue, basis.AxisU, basis.AxisV, basis.NormalValue)))
    blocked = guard_runtime()
    observations = []
    refusals = 0
    for invalid in (0, -0.001, float("inf"), True):
        try:
            make_section(invalid)
        except ValueError:
            refusals += 1
        else:
            raise ValueError("neutral section accepted an invalid radius")
    for radius in RADII:
        raw = make_section(radius)
        outer = wrap_section(raw)
        require(raw == make_section(radius) and outer == wrap_section(make_section(radius)),
                "model-only section is not deterministic")
        cursor = BinaryReader(outer)
        read = section_transport(cursor)
        found = transport({"fc8": read}, radius, frame)
        body = read["nodes"][0].fields
        require(cursor.GetRemaining() == 0 and body["owner"] == body["next"] == 0
                and body["highest_node_id"] == max(node.fields.get("node_id", 0) for node in read["nodes"])
                and found["radius_m"] == radius and found["normal"] == (1.0, 0.0, 0.0),
                "neutral section did not retain the closed local carrier graph")
        decoded, diagnostic = ReadBrepResult(raw)
        require(decoded is None, "standalone SDK boundary for neutral section changed")
        observations.append({
            "radius_m": radius, "area_m2": pi * radius ** 2,
            "raw_sha256": digest(raw), "raw_bytes": len(raw),
            "outer_sha256": digest(outer), "outer_bytes": len(outer),
            "model_next": body["next"], "model_highest_node_id": body["highest_node_id"],
            "typed_sheet": found, "standalone_brep_diagnostic": diagnostic,
            "existing_generic_sheet": compare_historical(radius, frame),
        })
    require(len({row["outer_bytes"] for row in observations}) == len(RADII)
            and not blocked, "neutral sizes did not vary independently or accessed external inputs")
    return {"mode": "model only section", "completed": len(observations), "observations": observations,
            "invalid_radius_refusals": refusals,
            "blocked_runtime_calls": len(blocked), "generated_part_count": 0}


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--disclosed", type=Path)
    mode.add_argument("--model-only", action="store_true")
    mode.add_argument("--emit-raw-radius-m", type=float)
    args = parser.parse_args()
    check_sdk()
    if args.emit_raw_radius_m is not None:
        blocked = guard_runtime()
        data = make_section(args.emit_raw_radius_m)
        require(not blocked, "neutral section accessed external inputs")
        sys.stdout.buffer.write(data)
        return
    result = compare_disclosed(args.disclosed) if args.disclosed else compare_model()
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
