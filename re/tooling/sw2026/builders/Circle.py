from __future__ import annotations

from collections.abc import Mapping
from math import hypot, isfinite

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


def bind_permanence(*, sketch, points, arcs):
    roles = tuple(point for arc in arcs for point in (arc["_start"], arc["_end"], arc["_center"]))
    order = NodeOrder(nodes=tuple({id(point): point for point in roles}.values()))
    centers = tuple(arc["_center"] for arc in arcs)
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
        marker = arc["_start"]
        marker["h1"] = arc_handle(sketch=sketch, arc=arc, arcs=arcs)
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
    sketch["_profile_kind"] = "circle" if len(arcs) == 1 else "circle_set"


def circle_positions(*, center_m, radius_m, frame):
    center_position = _vector(value=center_m, size=2)
    if type(radius_m) not in (int, float) or not isfinite(radius_m) or radius_m <= 0:
        raise ConstructionError("circle radius must be finite and positive")
    marker_position = _vector(value=(center_position[0] + radius_m, center_position[1]), size=2)
    if marker_position == center_position:
        raise ConstructionError("circle radius is not representable at this center")
    for position in (center_position, marker_position):
        frame.world_point(point=position)
    return center_position, marker_position


def circle_set_profile(*, circles_m, profile, plane, frame):
    if profile.cls != "moProfileFeature_c" or not isinstance(frame, PlaneFrame):
        raise ConstructionError("circle sketches require an ordinary allocated profile and frame")
    if not isinstance(circles_m, (tuple, list)) or not 1 <= len(circles_m) < 0x3FFFFFFF:
        raise ConstructionError("circle sets require a nonempty bounded sequence")
    positions = []
    for circle in circles_m:
        if not isinstance(circle, Mapping) or set(circle) != {"center_m", "radius_m"}:
            raise ConstructionError("circle set members require exactly center_m and radius_m")
        positions.append(circle_positions(**circle, frame=frame))
    for index, (center, marker) in enumerate(positions):
        radius = circles_m[index]["radius_m"]
        for previous in range(index):
            other = positions[previous][0]
            if hypot(center[0] - other[0], center[1] - other[1]) <= radius + circles_m[previous]["radius_m"]:
                raise ConstructionError("this circle set rung requires disjoint circles with distinct centers")
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    pairs = tuple((ordinary_point(sketch=graph.sketch, position=center), ordinary_point(sketch=graph.sketch, position=marker)) for center, marker in positions)
    points = NodeOrder(nodes=tuple(point for pair in pairs for point in pair))
    arcs = NodeOrder(nodes=tuple(circle_arc(sketch=graph.sketch, center=center, marker=marker, points=points) for center, marker in pairs))
    bind_permanence(sketch=graph.sketch, points=points, arcs=arcs)
    bind_arrays(sketch=graph.sketch, points=points, arcs=arcs)
    _bind_local_ref_flag(sketch=graph.sketch)
    graph.sketch["_requires_update"] = True
    return graph


def circle_profile(*, center_m, radius_m, profile, plane, frame):
    return circle_set_profile(circles_m=({"center_m": center_m, "radius_m": radius_m},), profile=profile, plane=plane, frame=frame)
