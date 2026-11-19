from collections import Counter
from hashlib import sha256
from itertools import product
from math import fsum
from pathlib import Path
import argparse
import json

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
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
    for node in nodes.values():
        if node.kind != 81 or definitions[node.fields["definition"]] != "FACE_ID_2001":
            continue
        owner = nodes[node.fields["owner"]]
        surface = nodes[owner.fields["surface"]]
        if surface.kind != 50:
            continue
        offset = fsum((p - q) * a for p, q, a in
                      zip(surface.fields["pvec"], cylinder["pvec"], cylinder["axis"], strict=True))
        kind, _, _, _, selector, contour = nodes[node.fields["fields"][2]].fields["values"]
        assert kind == 40 and contour == 0
        caps.append((offset, selector))
    near, far = sorted(caps)
    assert near == (0.0, 1) and far[0] > 0.0 and far[1] == 0
    return {"topology_counts": expected, "cap_offset_and_selector": [near, far]}


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
        stream = SldprtArchive.from_bytes(data).require(name)
        expected = tuple(payload.data for payload in DecodePartition(stream, name))
        partition = read_partition(stream)
        assert len(expected) == 2 and write_payloads(partition) == expected
        results.append({"case": case, "phase": phase, "sha256": control["sha256"],
                        "typed_payloads_exact": len(expected), **cap_identity(partition)})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("disclosed", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.disclosed), indent=2, allow_nan=False, sort_keys=True))
