from hashlib import sha256
import json
from math import isclose, sqrt

from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.Reading.ReadAdapter import BrepPayloadA
from convert.adapters.solidworks.Core.Partition.ActivePartition import ReadActivePart
from convert.adapters.solidworks.Archive.Partition.Current.Attributed.ReadActiveRows import ReadActiveRows
from FixtureGeometry import signed_geometry
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings

STREAM = "Contents/Config-0-Partition"
BODY = "sldprt:fixture:body:1"


def load_fixture(root):
    folder = root / "re/solidworks/Fixtures/PartitionAttributes"
    manifest_raw = (folder / "Manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    assert manifest["schema"] == "kit.research.solidworks.attributed-active-member-fixture.v1"
    assert manifest["member"]["file"] == "P03ActivePartition.bin"
    raw = (folder / manifest["member"]["file"]).read_bytes()
    assert len(raw) == manifest["member"]["bytes"] == 3955
    assert sha256(raw).hexdigest() == manifest["member"]["sha256"] == "d638c0c902a737e950ac0c9230f69fec746c54c111a6f52febf7c79472517729"
    native = DecodePartition(raw, STREAM)
    assert [(p.kind, p.sha256, len(p.data), p.wrapper_offset, p.stored_size) for p in native] == [
        (p["kind"], p["sha256"], p["clear_bytes"], p["wrapper_offset"], p["stored_bytes"]) for p in manifest["decoded_frames"]]
    return folder, manifest_raw, raw, native


def bind(native, config=0, body=BODY):
    payloads = tuple(BrepPayloadA(i, value) for i, value in enumerate(native))
    result = ReadActivePart(payloads, config, body, (STREAM,))
    return result, payloads


def assert_geometry(model):
    assert model is not None and not model.validate(frozenset((BODY,)))
    assert len(model.bodies) == 1 and model.bodies[0].design_body_id == BODY
    assert [len(model.faces), len(model.edges), len(model.vertices)] == [6, 12, 8]
    assert all(s.closed for s in model.shells)
    count, volume = signed_geometry(model)
    assert count == 6 and isclose(volume, 9600.0, rel_tol=0.0, abs_tol=1e-8)
    area = 0.0
    for ring in ReadMassRings(model):
        points = [(p.x, p.y, p.z) for p in ring]
        normal = [0.0, 0.0, 0.0]
        for a, b in zip(points, points[1:] + points[:1], strict=True):
            normal[0] += a[1] * b[2] - a[2] * b[1]
            normal[1] += a[2] * b[0] - a[0] * b[2]
            normal[2] += a[0] * b[1] - a[1] * b[0]
        assert sum(n * (v - c) for n, v, c in zip(normal, points[0], (20.0, 10.0, 6.0), strict=True)) > 0.0
        area += sqrt(sum(n * n for n in normal)) / 2.0
    assert isclose(area, 3040.0, rel_tol=0.0, abs_tol=1e-8)
    positions = {(v.point.x, v.point.y, v.point.z) for v in model.vertices}
    assert positions == {(x, y, z) for x in (0.0, 40.0) for y in (0.0, 20.0) for z in (0.0, 12.0)}
    expected = {127: 205914419, 98: 200278323, 125: 206831923, 108: 207094067, 109: 207356211, 49: 207618355}
    ranks = [127, 98, 125, 108, 109, 49]
    for face in model.faces:
        reference = int(face.id.rsplit(":", 1)[1])
        assert face.attributes["solidworks.unchanged_id"] == expected[reference]
        assert face.attributes["solidworks.unchanged_order"] == ranks.index(reference)
        assert face.attributes["solidworks.downstream_order"] == ranks.index(reference)
        assert "solidworks.colour_order" not in face.attributes
    return volume


def assert_fixture(native):
    active, = (p for p in native if p.kind == "partition")
    nodes, _ = ReadActiveRows(active.data)
    assert len(nodes) == 189
    owners = sum(n.KindValue == 81 for n in nodes.values())
    values = sum(n.KindValue in (82, 83, 84, 98) for n in nodes.values())
    assert owners == 33 and values == 32
    result, payloads = bind(native)
    assert result is not None and result.PayloadId == payloads[0].id
    volume = assert_geometry(result.ModelValue)
    assert [(p.kind, p.sha256, p.data) for p in payloads] == [(p.kind, p.sha256, p.data) for p in native]
    return active, result.ModelValue, owners, values, volume
