from collections import Counter
from hashlib import sha256
from json import loads
from math import fsum, pi

from VerifyLocalPocket import ROOT, counts, fingerprint
from convert.Geometry.Parasolid import DecodeBrepModel, DecodePartData
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import ReadBodyFaces

P04 = ROOT / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
D19 = ROOT / "re/solidworks/v2026/corpus/curves-discovery"
P04_SHA = "e1f431f1f21ae294fbd3711503ce386bec4fb4916c3cc83b57c876f1ae283149"
D19_SHA = "2a9846fa9ddc882ef3b848dfc311a7859d102ab9fa7687769cdba88a7b510439"
SCHEMA = "SCH_3701250_37102_13006"


def area_and_rings(nodes, owner, periodic):
    fin = RequireXmt(nodes, owner.Integer("halfedge"), 17)
    assert fin.Integer("loop") == owner.IndexValue
    if periodic:
        edge = RequireXmt(nodes, fin.Integer("edge"), 16)
        circle = RequireXmt(nodes, edge.Integer("curve"), 31)
        assert fin.Integer("forward") == fin.IndexValue
        return pi * (circle.FieldsValue["radius"] * 1000) ** 2, ()
    points = []
    first = fin.IndexValue
    for _ in range(4):
        assert fin.Integer("loop") == owner.IndexValue
        vertex = RequireXmt(nodes, fin.Integer("vertex"), 18)
        points.append(RequireXmt(nodes, vertex.Integer("point"), 29).FieldsValue["pvec"])
        fin = RequireXmt(nodes, fin.Integer("forward"), 17)
    assert fin.IndexValue == first and len(set(points)) == 4
    assert len({z for _, _, z in points}) == 1
    area = fsum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1])) * 5e5
    return area, tuple(sorted((x * 1000, y * 1000) for x, y, _ in points))


def cap_chains(nodes):
    caps = []
    for face in (node for node in nodes.values() if node.KindValue == 14):
        surface = nodes[face.Integer("surface")]
        if surface.KindValue != 50:
            continue
        loops = WalkXmtChain(nodes, face.Integer("loop"), 15, PreviousField=None,
                             OwnerField="face", OwnerValue=face.IndexValue)
        if len(loops) == 1:
            continue
        assert len(loops) == 2 and surface.Integer("owner") == face.IndexValue
        z = surface.FieldsValue["pvec"][2]
        normal = surface.FieldsValue["normal"]
        sense = face.String("sense")
        effective = tuple(value if sense == "+" else -value for value in normal)
        assert effective in ((0., 0., 1.), (0., 0., -1.))
        caps.append((z, face.IndexValue, loops, effective[2], sense, normal))
    assert len(caps) == 2
    caps.sort()
    assert tuple(row[3] for row in caps) == (-1, 1) and caps[0][0] < caps[1][0]
    return caps


def observe_file(path, pin, periodic):
    source = path.read_bytes()
    assert sha256(source).hexdigest() == pin
    archive = SldprtArchive.from_bytes(source)
    active, delta = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    assert archive.format_version == 4 and (active.kind, delta.kind) == ("partition", "deltas")
    assert active.schema == delta.schema == SCHEMA
    nodes = ReadActiveNodes(active.data)
    body, = (node for node in nodes.values() if node.KindValue == 12 and node.Integer("edge"))
    sizes = Counter(node.KindValue for node in nodes.values())
    assert set(ReadBodyFaces(nodes, body, sizes[14])) == {node.IndexValue for node in nodes.values() if node.KindValue == 14}
    skin = DecodeBrepModel(active.data)
    assert skin is not None and len(skin.bodies) == 1 and skin.regions[0].solid
    cap_stats = []
    for z, face_id, loop_ids, sense, face_sense, normal in cap_chains(nodes):
        areas, rings = zip(*(area_and_rings(nodes, nodes[index], periodic) for index in loop_ids))
        assert all(value for value in areas)
        if not periodic:
            assert tuple(sense * value > 0 for value in areas) == (False, True)
            assert abs(areas[0]) < abs(areas[1])
        cap_stats.append({"face": face_id, "ordered_loops": loop_ids, "plane_height_mm": z * 1000,
                          "signed_effective_normal_z": sense, "native_surface_normal": normal,
                          "native_face_sense": face_sense, "xy_corners_mm": rings, "areas_mm2": areas})
    if not periodic:
        assert counts(skin) == (10, 12, 24, 48, 16)
        assert cap_stats[0]["xy_corners_mm"] == cap_stats[1]["xy_corners_mm"]
        assert all(tuple(round(abs(value), 9) for value in row["areas_mm2"]) == (80., 800.) for row in cap_stats)
        roles = {loop.id: loop.outer for loop in skin.loops}
        assert [tuple(roles[key] for key in face.loop_ids) for face in skin.faces if len(face.loop_ids) == 2] == [(False, True)] * 2
    return {"source": fingerprint(source), "active": fingerprint(active.data), "deltas": fingerprint(delta.data),
            "schema": active.schema, "body_kind": body.Integer("body_type"), "body_id": body.IndexValue,
            "topology": counts(skin), "plane_caps": cap_stats}


def observe():
    p04_receipt = (P04 / "receipt.json").read_bytes()
    p04_measures = (P04 / "measurements.json").read_bytes()
    p04 = loads(p04_receipt)
    native = loads(p04_measures)
    assert p04["errors"] == 0 and sha256(p04_measures).hexdigest() == p04["measurement_receipt_sha256"]
    native_row, = (row for row in p04["native_files"] if row["sha256"] == P04_SHA)
    assert (native_row["save_errors"], native_row["save_warnings"]) == (0, 0)
    assert native["executable_file_version"] == "34.4.1.1011"
    manifest_data = (D19 / "Manifest.json").read_bytes()
    manifest = loads(manifest_data)
    d19_row, = (row for row in manifest["records"] if row["name"] == "D19Annulus")
    assert manifest["native_build"] == "34.5.2.0604" and d19_row["sha256"] == D19_SHA
    return {
        "rectangular_passage": {"build": native["executable_file_version"],
                                "receipt": fingerprint(p04_receipt), "measurement_receipt": fingerprint(p04_measures),
                                **observe_file(P04 / native_row["file"], P04_SHA, False)},
        "sp052_annulus_cap_links": {"build": manifest["native_build"], "manifest": fingerprint(manifest_data),
                                   **observe_file(D19 / d19_row["file"], D19_SHA, True)},
    }
