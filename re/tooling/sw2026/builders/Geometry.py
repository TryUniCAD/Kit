from __future__ import annotations

from Core import Obj
from builders.Sketch import ConstructionError, DerivedFields, NodeOrder, _node_index, line_handle


def arc_handle(*, sketch, arc, arcs):
    if sketch.cls != "sgSketch" or arc.cls != "sgArc" or arc.get("_sketch") is not sketch:
        raise ConstructionError("arc handles require a locally owned arc node")
    return Obj("sgArcHandle", DerivedFields(
        fields={"_sketch": sketch, "_arc": arc, "f1c": -1, "f08": 0},
        derived={
            "idx": lambda: min(_node_index(nodes=arcs, node=arc), 0x777F),
            "f18": lambda: _node_index(nodes=arcs, node=arc),
        },
    ))


def bind_permanence(*, sketch, points, arcs, lines=None):
    lines = NodeOrder(nodes=()) if lines is None else lines
    segments = NodeOrder(nodes=(*lines, *arcs))
    if any(node.cls not in ("sgLine", "sgArc") or node.get("_sketch") is not sketch for node in segments):
        raise ConstructionError("permanence requires locally owned ordinary lines and arcs")
    roles = tuple(point for node in segments for point in ((node["_start"], node["_end"], node["_center"]) if node.cls == "sgArc" else (node["_start"], node["_end"])))
    for point in roles:
        _node_index(nodes=points, node=point)
    order = NodeOrder(nodes=tuple({id(point): point for point in roles}.values()))
    centers = tuple(arc["_center"] for arc in arcs)
    incident = {id(point): [] for point in points}
    for segment in segments:
        endpoints = tuple({id(point): point for point in (segment["_start"], segment["_end"])}.values())
        for point in endpoints:
            incident[id(point)].append(segment)
    for point in points:
        neighbors = incident[id(point)]
        if len(neighbors) > 2 or point["h1"] is not None or point["h2"] is not None:
            raise ConstructionError("ordinary endpoint adjacency requires at most two fresh incident segments")
        if neighbors and any(center is point for center in centers):
            raise ConstructionError("this curve rung keeps center roles separate from endpoints")
        if sum(role is point for role in roles) > 0xFFFF or sum(center is point for center in centers) > 0xFFFF:
            raise ConstructionError("point role counts exceed their wire width")
        for name in ("f0c", "fe8", "fec"):
            del point.f[name]
        point.f = DerivedFields(fields=point.f, derived={
            "f0c": lambda node=point: _node_index(nodes=order, node=node) + 1,
            "fe8": lambda node=point: sum(item is node for item in roles),
            "fec": lambda node=point: sum(item is node for item in centers),
        })
        for slot, segment in zip(("h1", "h2"), neighbors):
            point[slot] = line_handle(sketch=sketch, line=segment, lines=lines) if segment.cls == "sgLine" else arc_handle(sketch=sketch, arc=segment, arcs=arcs)
        if any(segment.cls == "sgArc" and segment["_ordinary_circle"] for segment in neighbors):
            if len(neighbors) != 1:
                raise ConstructionError("full-circle markers cannot share another endpoint role in this rung")
            point["fe4"] = 2
    for segment in segments:
        own = lines if segment.cls == "sgLine" else arcs
        for name in ("f0c", "f08"):
            del segment.f[name]
        segment.f.derived["f0c"] = lambda node=segment, nodes=own: _node_index(nodes=nodes, node=node) + 1
        segment.f.derived["f08"] = lambda node=segment: _node_index(nodes=segments, node=node) + 1
        if segment.cls == "sgLine":
            del segment.f["fd0"]
            segment.f.derived["fd0"] = lambda node=segment: int(all(any(point[slot] is not None and point[slot].get("_line") is node for slot in ("h1", "h2")) for point in (node["_start"], node["_end"])))


def bind_arrays(*, sketch, points, arcs, lines=None):
    lines = NodeOrder(nodes=()) if lines is None else lines
    if any(len(nodes) >= 0x7FFFFFFF for nodes in (points, lines, arcs)) or len(lines) + len(arcs) >= 0x7FFFFFFF:
        raise ConstructionError("geometry arrays exceed signed next-counter width")
    records = {
        "points": tuple({"kind": 0, "point": node.f} for node in points),
        "lines": tuple({"flags": 0, "line": node.f} for node in lines),
        "arcs": tuple({"flags": 0, "arc": node.f} for node in arcs),
    }
    for name in (*records, "f130", "f56c"):
        del sketch.f[name]
    for name, rows in records.items():
        sketch.f.derived[name] = lambda values=rows: values
    sketch.f.derived.update({"f130": lambda: len(lines) + len(arcs) + 1, "f56c": lambda: 1 + len(lines) + len(arcs)})
    counters = dict(sketch["f140"])
    for name in ("f08", "f0c", "f10"):
        del counters[name]
    sketch["f140"] = DerivedFields(fields=counters, derived={
        "f08": lambda: len(points) + 1, "f0c": lambda: len(lines) + 1, "f10": lambda: len(arcs) + 1,
    })
    sketch["_point_nodes"] = points
    sketch["_line_nodes"] = lines
    sketch["_arc_nodes"] = arcs
    if lines:
        sketch["_profile_kind"] = "mixed" if arcs else "lines"
    else:
        kind = "circle" if all(arc["_ordinary_circle"] for arc in arcs) else "arc"
        sketch["_profile_kind"] = kind if len(arcs) == 1 else kind + "_set"
