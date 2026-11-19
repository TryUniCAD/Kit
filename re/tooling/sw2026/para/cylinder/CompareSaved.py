from collections import Counter
from hashlib import sha256
from itertools import product
from math import fsum
from pathlib import Path
import argparse
import json

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import ReadCylOwner
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from para.Partition import read_partition, write_payloads


def cap_identity(partition):
    nodes = {node.index: node for node in partition.nodes}
    counts = Counter(node.kind for node in nodes.values())
    expected = {12: 1, 13: 2, 14: 3, 15: 4, 16: 2, 17: 4, 18: 0, 19: 2, 29: 0, 31: 2, 50: 2, 51: 1}
    assert all(counts[kind] == count for kind, count in expected.items())
    cylinder, = (node.fields for node in nodes.values() if node.kind == 51)
    definitions = {node.index: nodes[node.fields["identifier"]].fields["string"]
                   for node in nodes.values() if node.kind == 80}
    caps = []
    side_allocations = []
    for node in nodes.values():
        if node.kind != 81 or definitions[node.fields["definition"]] != "FACE_ID_2001":
            continue
        owner = nodes[node.fields["owner"]]
        surface = nodes[owner.fields["surface"]]
        ordinal, external = nodes[node.fields["fields"][3]].fields["values"]
        assert external == 0
        if surface.kind != 50:
            assert surface.kind == 51
            side_allocations.append(ordinal)
            continue
        offset = fsum((p - q) * a for p, q, a in
                      zip(surface.fields["pvec"], cylinder["pvec"], cylinder["axis"], strict=True))
        kind, _, _, _, selector, contour = nodes[node.fields["fields"][2]].fields["values"]
        assert kind == 40 and contour == 0
        caps.append((offset, selector, ordinal))
    near, far = sorted(caps)
    assert near[:2] == (0.0, 1) and far[0] > 0.0 and far[1] == 0
    side, = side_allocations
    assert side == far[2] + 1 == near[2] + 2
    return {"topology_counts": expected, "cap_offset_and_selector": [near[:2], far[:2]],
            "face_allocation_order": ["sketch_plane", "far_plane", "lateral"],
            "observed_auxiliary_ids_in_order": [near[2], far[2], side]}


def body_attachment(archive, partition):
    link = ReadNativeLink(archive, 0)
    model = link.ConfigValue.RootValue.FieldsValue
    nodes = ReadCylNodes(archive)
    _, _, body = PickCylFace(nodes)
    names = ("ATOM_ID_2001", "BODY_MATCH", "ENT_TIME_STAMP_2001", "LAST_BODY_MODIFYING_FEATURE_ID")
    attributes = {name: ReadCylAttr(nodes, body, name) for name in names}
    atom_id, tag, stamp, modifier = (ReadBodyScalar(nodes, attributes, name, lane)
                                    for name, lane in zip(names, (1, 0, 1, 1), strict=True))
    feature, _ = ReadCylOwner(link, atom_id)
    atom = ReadOutputAtom(feature)
    selected, _, activation = partition.history
    assert atom is model["fd88"]["atoms"][0]["o"] is model["ffe0"][0]["k"]
    assert atom.FieldsValue["f180"] == atom.FieldsValue["f1b0"] == tag
    assert modifier == feature.FieldsValue["f08"] and feature.FieldsValue["f498"] == [{"v": atom_id}]
    assert stamp == link.ConfigValue.HeaderValue.FieldsValue["f44"]
    assert activation.mark.fields["id"] == model["fe38"].FieldsValue["f18"]
    assert selected.mark.fields["id"] == feature.FieldsValue["f3d0"].FieldsValue["f18"]
    return {"atom_id": atom_id, "body_match": tag, "body_stamp": stamp,
            "marks": [activation.mark.fields["id"], selected.mark.fields["id"]],
            "manager_output_visibility_same_object": True}


def compare(disclosed):
    results = []
    for case, phase in product(("D01", "D02", "D03"), ("source", "edited")):
        folder = disclosed / case
        lock = json.loads((folder / "lock.json").read_bytes())
        assert lock["source_locked"] and not lock["heldout_source_locked"]
        control = lock["native_artifacts"][phase]["child"]
        part = folder / "Native" / phase.title() / f"Concentric{case}Child.SLDPRT"
        data = part.read_bytes()
        assert len(data) == control["bytes"] and sha256(data).hexdigest() == control["sha256"]
        name = "Contents/Config-0-Partition"
        archive = SldprtArchive.from_bytes(data)
        stream = archive.require(name)
        expected = tuple(payload.data for payload in DecodePartition(stream, name))
        partition = read_partition(stream)
        assert len(expected) == 2 and write_payloads(partition) == expected
        results.append({"case": case, "phase": phase, "sha256": control["sha256"],
                        "typed_payloads_exact": len(expected), **cap_identity(partition),
                        "body_attachment": body_attachment(archive, partition)})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("disclosed", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.disclosed), indent=2, allow_nan=False, sort_keys=True))
