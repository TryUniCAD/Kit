from hashlib import sha256
from itertools import product
from math import isclose
from pathlib import Path
import argparse
import json

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar


def kernel_significant_fields(archive):
    nodes = ReadCylNodes(archive)
    side, carrier, body = PickCylFace(nodes)
    stamp = ReadBodyScalar(nodes, {"SWEntUnchanged": ReadCylAttr(nodes, side, "SWEntUnchanged")}, "SWEntUnchanged", 0)
    body_tag = ReadBodyScalar(nodes, {"BODY_MATCH": ReadCylAttr(nodes, body, "BODY_MATCH")}, "BODY_MATCH", 0)
    order, cap_spans = [], []
    initial = carrier.FieldsValue["pvec"]
    axis = carrier.FieldsValue["axis"]
    loop = side.Integer("loop")
    while loop:
        member = nodes[loop]
        fin = nodes[member.Integer("halfedge")]
        other = nodes[fin.Integer("other")]
        cap = nodes[nodes[other.Integer("loop")].Integer("face")]
        plane = nodes[cap.Integer("surface")]
        assert plane.KindValue == 50 and cap is not side
        kind, _, _, _, selector, contour = ReadCylWords(nodes, cap)
        assert kind == 40 and contour == 0 and selector not in order
        order.append(selector)
        rim = nodes[nodes[fin.Integer("edge")].Integer("curve")]
        cap_spans.append(sum((p - q) * a for p, q, a in zip(rim.FieldsValue["centre"], initial, axis, strict=True)))
        loop = member.Integer("next")
    assert order == [1, 0] and cap_spans[0] == 0.0
    return order, cap_spans[1], (stamp >> 16) & 0xffff, body_tag


def compare_parent(section, kernel):
    expected_order, length, tag_low, body_tag = kernel
    graph = section["graph"]

    def fields(entry):
        return graph[str(entry["index"])]["fields"]

    root = fields(section["root"])
    result = []
    for chosen, backup in zip(root["f410"], root["f3c8"], strict=True):
        active, support = fields(chosen["o"]), fields(backup["o"])
        active_component = fields(active["f58"])
        support_component = fields(support["f58"])
        face = fields(active_component["fe8"])
        face_rows = face["f10"]
        assert face_rows[2]["f08"] is face_rows[4]["f08"] is None
        cap_order = [fields(face_rows[index]["f08"])["f38"] for index in (1, 3)]
        assert cap_order == expected_order
        face_tag = face["f70"]
        assert face_tag & 0xffff == tag_low
        assert active["f10"] == active["f18"] == support_component["fc8"]
        interval = tuple(active[name] for name in ("fb0", "fb8", "fc0", "fc8"))
        neutral = tuple(support[name] for name in ("fb0", "fb8", "fc0", "fc8"))
        assert interval[0] == 0 and isclose(interval[1], length, abs_tol=1e-15, rel_tol=1e-12)
        assert interval[2:] == (1.0, -1.0) and neutral == (-1.0, 1.0, 1.0, -1.0)
        assert active["has_f108"] == 1 and support["has_f108"] == 0
        result.append({"cap_order": cap_order, "tag_low_matches": True, "face_tag": face_tag,
                       "body_tag": body_tag, "active_surface_tail": interval, "support_surface_tail": neutral})
    return result


def audit(root):
    graph_raw = (root / "DisclosedTypedGraph01.json").read_bytes()
    graph_sha = sha256(graph_raw).hexdigest()
    assert graph_sha == "5a28338afa61c3b71daa0059970321e8134b3ace275ebc6f3f36dac0fef8ce4b"
    source = json.loads(graph_raw)
    cases = []
    for case, phase in product(("D01", "D02", "D03"), ("source", "edited")):
        lane = root / "Disclosed" / case
        lock = json.loads((lane / "lock.json").read_bytes())
        assert lock["source_locked"] and not lock["heldout_source_locked"]
        data = (lane / "Native" / phase.title() / f"Concentric{case}Child.SLDPRT").read_bytes()
        digest = sha256(data).hexdigest()
        assert digest == lock["native_artifacts"][phase]["child"]["sha256"]
        kernel = kernel_significant_fields(SldprtArchive.from_bytes(data))
        pairs = compare_parent(source[case][phase], kernel)
        cases.append({"case": case, "phase": phase, "child_sha256": digest,
                      "kernel_lateral_cap_order": kernel[0], "endpoints": pairs})
    return {"source_graph_sha256": graph_sha, "cases": cases, "read_saved_inputs_for_construction": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    print(json.dumps(audit(parser.parse_args().packet), indent=2, allow_nan=False, sort_keys=True))
