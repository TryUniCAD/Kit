from __future__ import annotations

from collections.abc import Mapping
from math import hypot, isfinite

from Core import Obj
from builders.Geometry import bind_arrays, bind_permanence
from builders.Sketch import (
    ConstructionError, DerivedFields, NodeOrder, PlaneFrame, _bind_local_ref_flag,
    _node_index, _vector, entity_fields, new_profile, ordinary_point,
)


def arc_node(*, sketch, center, start, end, points, orientation):
    if center is start or center is end or any(node.cls != "sgPoint" or node.get("_sketch") is not sketch for node in (center, start, end)):
        raise ConstructionError("an arc requires local endpoints distinct from its center")
    if type(orientation) is not int or orientation not in (-1, 1):
        raise ConstructionError("ordinary arc orientation must be signed unit direction")
    fields = entity_fields(sketch=sketch)
    fields.update({
        "_center": center, "_start": start, "_end": end,
        "_ordinary_arc": True, "_ordinary_circle": start is end,
        "fd4": 0, "seg_tol": -1.0, "fd8": orientation,
        "fe0": -2, "fe4": -2, "fe8": -2, "fec": -2,
    })
    derived = {"fd0": lambda: int(all(any(point[slot] is not None and point[slot].get("_arc") is arc for slot in ("h1", "h2")) for point in (start, end)))}
    for name, node in (("fc8", start), ("fcc", end), ("fdc", center)):
        derived[name] = lambda target=node: _node_index(nodes=points, node=target)
        derived[name + "_s"] = lambda target=node: min(_node_index(nodes=points, node=target), 0xFFFF)
    arc = Obj("sgArc", DerivedFields(fields=fields, derived=derived))
    return arc


def circle_arc(*, sketch, center, marker, points):
    return arc_node(sketch=sketch, center=center, start=marker, end=marker, points=points, orientation=1)


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
