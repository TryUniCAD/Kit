from collections import Counter
from hashlib import sha256
from io import BytesIO
from math import isclose, pi
from pathlib import PureWindowsPath
import argparse
import codecs
import json
import sys

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep, DecodePartition
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from FreshCylinderInput import make_document
from para.Partition import read_partition, write_payloads
from para.cylinder.ProjectCylinder import project_cylinder
from para.rectangle.Allocate import DeltaEvent, MarkEvent, Session


CASES = {
    "FrontDiameter": ("z", "Front Plane", (3.46, -6.91), 4.783, 18.427, "diameter", False, 1805300101, 26, 0),
    "OffsetFrontDiameter": ("z", "Front Plane", (-12.75, 4.375), 6.125, 9.625, "diameter", False, 1805337313, 117, 11),
    "ReverseTop": ("y", "Top Plane", (-9.283, 2.467), 8.9165, 11.073, "radius", True, 1805307307, 203, 24),
}
STREAM = "Contents/Config-0-Partition"


def close_values(actual, expected):
    return all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(actual, expected, strict=True))


def inspect_geometry(nodes, face, cylinder, body, spec):
    counts = Counter(node.KindValue for node in nodes.values())
    expected = {12: 1, 13: 2, 14: 3, 15: 4, 16: 2, 17: 4, 18: 0, 19: 2, 29: 0, 31: 2, 50: 2, 51: 1}
    assert all(counts[kind] == count for kind, count in expected.items())
    assert body.Integer("vertex") == body.Integer("boundary_point") == 0
    for fin in (node for node in nodes.values() if node.KindValue == 17):
        assert fin.Integer("forward") == fin.Integer("backward") == fin.IndexValue
        assert fin.Integer("vertex") == fin.Integer("next_at_vx") == 0
        opposite = nodes[fin.Integer("other")]
        assert opposite.Integer("other") == fin.IndexValue and opposite.Integer("edge") == fin.Integer("edge")
        assert opposite.String("sense") != fin.String("sense")
    caps = [
        (item, nodes[item.Integer("surface")])
        for item in nodes.values()
        if item.KindValue == 14 and item is not face
    ]
    (start, start_plane), (end, end_plane) = sorted(caps, key=lambda pair: pair[1].FieldsValue["pvec"][2])
    start_xyz, end_xyz = (tuple(plane.FieldsValue["pvec"]) for plane in (start_plane, end_plane))
    centre = tuple(value / 1000 for value in spec["center_mm"])
    length, radius = spec["depth_mm"] / 1000, spec["radius_mm"] / 1000
    assert close_values(start_xyz, (*centre, 0)) and close_values(end_xyz, (*centre, length))
    assert (face.String("sense"), start.String("sense"), end.String("sense")) == ("+", "-", "+")
    assert all(close_values(plane.FieldsValue["normal"], (0, 0, 1)) for _, plane in caps)
    assert close_values(cylinder.FieldsValue["pvec"], start_xyz)
    assert close_values(cylinder.FieldsValue["axis"], (0, 0, 1))
    assert close_values((cylinder.FieldsValue["radius"],), (radius,))
    observed_circles = sorted(
        (node for node in nodes.values() if node.KindValue == 31),
        key=lambda node: node.FieldsValue["centre"][2],
    )
    for ring, point in zip(observed_circles, (start_xyz, end_xyz), strict=True):
        assert close_values(ring.FieldsValue["centre"], point)
        assert close_values(ring.FieldsValue["normal"], (0, 0, 1))
        assert close_values((ring.FieldsValue["radius"],), (radius,))
    decoded_length = end_xyz[2] - start_xyz[2]
    decoded_radius = cylinder.FieldsValue["radius"]
    volume = pi * decoded_radius**2 * decoded_length
    area = 2 * pi * decoded_radius * (decoded_radius + decoded_length)
    assert close_values((volume, area), (pi * radius**2 * length, 2 * pi * radius * (radius + length)))
    measured = {
        "center_m": (*start_xyz[:2], (start_xyz[2] + end_xyz[2]) / 2),
        "analytic_volume_m3": volume,
        "analytic_area_m2": area,
        "height_m": decoded_length,
        "radius_m": decoded_radius,
        "topology_counts": expected,
    }
    return start, end, measured


def inspect(candidate, projection, stream, spec, earlier_face_count):
    payloads = tuple(payload.data for payload in DecodePartition(stream, STREAM))
    partition = read_partition(stream)
    assert partition == projection.partition and write_payloads(partition) == payloads
    active, deltas = payloads
    nodes = ReadActiveNodes(active)
    CheckXmtGraph(nodes)
    ReadXmtHistory(deltas, nodes)
    side, cylinder, body = PickCylFace(nodes)
    CheckXmtAttrs(nodes, body)
    start, end, measured = inspect_geometry(nodes, side, cylinder, body, spec)
    feature_id = candidate.BossValue.FeatureValue.FieldsValue["f08"]
    epoch = DatumTime(candidate.HeaderValue, feature_id)
    arc = candidate.ProfileValue.GeometryValue.ArcValue.FieldsValue
    expected_words = ((74, feature_id, epoch, 0, arc["f08"]),
                      (40, feature_id, epoch, 0, 1, 0), (40, feature_id, epoch, 0, 0, 0))
    faces = (side, start, end)
    assert tuple(ReadCylWords(nodes, face) for face in faces) == expected_words
    auxiliaries = tuple(ReadCylWords(nodes, face, 3) for face in faces)
    assert auxiliaries == tuple((earlier_face_count + offset, 0) for offset in (1, 2, 3))
    face_id = side.Integer("node_id")
    assert face_id == projection.lateral_face_node_id and face_id != side.IndexValue
    attributes = {name: ReadCylAttr(nodes, body, name)
                  for name in ("ATOM_ID_2001", "LAST_BODY_MODIFYING_FEATURE_ID")}
    atom_id = ReadBodyScalar(nodes, attributes, "ATOM_ID_2001", 1)
    assert atom_id == projection.reserved_body_atom_id
    assert ReadBodyScalar(nodes, attributes, "LAST_BODY_MODIFYING_FEATURE_ID", 1) == feature_id
    brep = DecodeBrep(active)
    assert brep is not None and len(brep.bodies) == 1 and len(brep.faces) == 3
    assert len(brep.edges) == 2 and all(shell.closed for shell in brep.shells)
    assert sorted(len(face.loop_ids) for face in brep.faces) == [1, 1, 2]
    return {
        "geometry": measured, "typed_payloads_exact": len(payloads), "wire_face_index": side.IndexValue,
        "persistent_face_node_id": face_id, "reserved_body_atom_id": atom_id,
        "face_words": expected_words, "face_auxiliary_words": auxiliaries,
        "partition_bytes": len(stream), "partition_sha256": sha256(stream).hexdigest(),
        "public_brep_vertex_count": len(brep.vertices), "history_mark_count": len(partition.history),
    }


def run(case):
    axis, plane, centre, radius, depth, driver, reverse, stamp, delta, preceding = CASES[case]
    spec = {
        "case": case, "name": case, "axis": axis, "plane": plane, "center_mm": centre,
        "radius_mm": radius, "depth_mm": depth, "driver": driver, "reversed": reverse, "written_at": stamp,
    }
    document = make_document(spec)
    document.AssertValid()
    GetDocumentCaps(document)
    for encoding in ("utf-16-le", "utf-16-be", "cp1252"):
        codecs.lookup(encoding)
    options = WriteOptions(values={"final_destination": str(PureWindowsPath("C:/KitResearch", case + ".SLDPRT"))})
    session = Session(
        1, delta, (DeltaEvent("activation"), MarkEvent("activation", "activation", True),
                   DeltaEvent("geometry"), MarkEvent("geometry", "geometry", True)), (), stamp, 0,
    )
    attempts = []
    forbidden = {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}
    active = True

    def guard(event, values):
        if active and event in forbidden:
            attempts.append(event)
            raise RuntimeError(f"offline cylinder projection attempted {event}")

    sys.addaudithook(guard)
    try:
        candidate = PrepareNative(document, BytesIO(), stamp, options)
        try:
            projection = project_cylinder(candidate, session, preceding)
        except ValueError as exc:
            assert reverse and str(exc) == "cylinder cache experiment requires a generated forward blind Front diameter circle"
            proof = {"rejected_outside_profile": True}
        else:
            assert not reverse
            stream = projection.stream()
            assert stream == project_cylinder(candidate, session, preceding).stream()
            proof = inspect(candidate, projection, stream, spec, preceding)
            proof["same_process_repeat_exact"] = True
    finally:
        active = False
    assert not attempts and STREAM not in candidate.StreamsValue
    return {
        "case": case, "authored_input": spec,
        "allocation_context": {"next_delta_handle": delta, "previous_face_allocations": preceding},
        "neutral_document_sha256": sha256(document.to_json(indent=None).encode()).hexdigest(),
        "runtime_file_process_network_attempts": len(attempts),
        "ordinary_candidate_sha256": sha256(candidate.BytesValue).hexdigest(),
        "archive_atom_registered": False, "attached_partition": False, **proof,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES)
    args = parser.parse_args()
    print(json.dumps(run(args.case), indent=2, allow_nan=False, sort_keys=True))
