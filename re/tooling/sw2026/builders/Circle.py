from __future__ import annotations

from math import isfinite

from Core import Obj
from builders.Sketch import (
    ConstructionError, DerivedFields, NodeOrder, PlaneFrame, _bind_local_ref_flag,
    _node_index, _vector, entity_fields, new_profile, ordinary_point,
)


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


def circle_arc(*, sketch, center, marker, points):
    if center is marker or any(node.cls != "sgPoint" or node.get("_sketch") is not sketch for node in (center, marker)):
        raise ConstructionError("a circle requires distinct local center and marker points")
    fields = entity_fields(sketch=sketch)
    fields.update({
        "_center": center, "_start": marker, "_end": marker,
        "_ordinary_circle": True, "fd4": 0, "seg_tol": -1.0, "fd8": 1,
        "fe0": -2, "fe4": -2, "fe8": -2, "fec": -2,
    })
    derived = {"fd0": lambda: int(marker["h1"] is not None and marker["h1"].get("_arc") is arc)}
    for name, node in (("fc8", marker), ("fcc", marker), ("fdc", center)):
        derived[name] = lambda target=node: _node_index(nodes=points, node=target)
        derived[name + "_s"] = lambda target=node: min(_node_index(nodes=points, node=target), 0xFFFF)
    arc = Obj("sgArc", DerivedFields(fields=fields, derived=derived))
    return arc


def bind_permanence(*, sketch, points, arcs, marker, center):
    order = NodeOrder(nodes=(marker, center))
    roles = (marker, marker, center)
    centers = (center,)
    for point in points:
        del point.f["f0c"]
        del point.f["fe8"]
        del point.f["fec"]
        point.f = DerivedFields(fields=point.f, derived={
            "f0c": lambda node=point: _node_index(nodes=order, node=node) + 1,
            "fe8": lambda node=point: sum(item is node for item in roles),
            "fec": lambda node=point: sum(item is node for item in centers),
        })
    for arc in arcs:
        del arc.f["f0c"]
        del arc.f["f08"]
        arc.f.derived["f0c"] = lambda node=arc: _node_index(nodes=arcs, node=node) + 1
        arc.f.derived["f08"] = lambda node=arc: _node_index(nodes=arcs, node=node) + 1
    marker["h1"] = arc_handle(sketch=sketch, arc=arcs[0], arcs=arcs)
    marker["fe4"] = 2


def bind_arrays(*, sketch, points, arcs):
    point_records = tuple({"kind": 0, "point": node.f} for node in points)
    arc_records = tuple({"flags": 0, "arc": node.f} for node in arcs)
    del sketch.f["points"]
    del sketch.f["arcs"]
    del sketch.f["f130"]
    del sketch.f["f56c"]
    sketch.f.derived.update({
        "points": lambda: point_records,
        "arcs": lambda: arc_records,
        "f130": lambda: len(arcs) + 1,
        "f56c": lambda: 1 + len(arcs),
    })
    counters = dict(sketch["f140"])
    del counters["f08"]
    del counters["f10"]
    sketch["f140"] = DerivedFields(fields=counters, derived={
        "f08": lambda: len(points) + 1, "f10": lambda: len(arcs) + 1,
    })
    sketch["_point_nodes"] = points
    sketch["_line_nodes"] = NodeOrder(nodes=())
    sketch["_arc_nodes"] = arcs
    sketch["_profile_kind"] = "circle"


def circle_profile(*, center_m, radius_m, profile, plane, frame):
    if profile.cls != "moProfileFeature_c" or not isinstance(frame, PlaneFrame):
        raise ConstructionError("circle sketches require an ordinary allocated profile and frame")
    center_position = _vector(value=center_m, size=2)
    if type(radius_m) not in (int, float) or not isfinite(radius_m) or radius_m <= 0:
        raise ConstructionError("circle radius must be finite and positive")
    marker_position = _vector(value=(center_position[0] + radius_m, center_position[1]), size=2)
    if marker_position == center_position:
        raise ConstructionError("circle radius is not representable at this center")
    for position in (center_position, marker_position):
        frame.world_point(point=position)
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    center = ordinary_point(sketch=graph.sketch, position=center_position)
    marker = ordinary_point(sketch=graph.sketch, position=marker_position)
    points = NodeOrder(nodes=(center, marker))
    arcs = NodeOrder(nodes=(circle_arc(sketch=graph.sketch, center=center, marker=marker, points=points),))
    bind_permanence(sketch=graph.sketch, points=points, arcs=arcs, marker=marker, center=center)
    bind_arrays(sketch=graph.sketch, points=points, arcs=arcs)
    _bind_local_ref_flag(sketch=graph.sketch)
    graph.sketch["_requires_update"] = True
    return graph
