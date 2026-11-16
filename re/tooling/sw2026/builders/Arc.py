from __future__ import annotations

from math import cos, isfinite, sin, tau

from builders.Circle import arc_node, bind_arrays, bind_permanence
from builders.Sketch import (
    ConstructionError, NodeOrder, PlaneFrame, _bind_local_ref_flag, _vector,
    new_profile, ordinary_point,
)


def open_arc_profile(*, center_m, radius_m, start_angle_rad, sweep_angle_rad, profile, plane, frame):
    if profile.cls != "moProfileFeature_c" or not isinstance(frame, PlaneFrame):
        raise ConstructionError("open arcs require an ordinary allocated profile and frame")
    center_position = _vector(value=center_m, size=2)
    for value in (radius_m, start_angle_rad, sweep_angle_rad):
        if type(value) not in (int, float) or not isfinite(value):
            raise ConstructionError("arc radius and angles must be finite numbers")
    if radius_m <= 0 or not 0 < abs(sweep_angle_rad) < tau:
        raise ConstructionError("open arcs require positive radius and a nonzero sweep below one full turn")
    positions = [center_position]
    for angle in (start_angle_rad, start_angle_rad + sweep_angle_rad):
        if not isfinite(angle):
            raise ConstructionError("arc endpoint angle must be finite")
        point = _vector(value=(center_position[0] + radius_m * cos(angle), center_position[1] + radius_m * sin(angle)), size=2)
        if point in positions:
            raise ConstructionError("arc points must be representably distinct")
        positions.append(point)
    for point in positions:
        frame.world_point(point=point)
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    points = NodeOrder(nodes=tuple(ordinary_point(sketch=graph.sketch, position=point) for point in positions))
    center, start, end = points
    arcs = NodeOrder(nodes=(arc_node(sketch=graph.sketch, center=center, start=start, end=end, points=points, orientation=1 if sweep_angle_rad > 0 else -1),))
    bind_permanence(sketch=graph.sketch, points=points, arcs=arcs)
    bind_arrays(sketch=graph.sketch, points=points, arcs=arcs)
    _bind_local_ref_flag(sketch=graph.sketch)
    graph.sketch["_requires_update"] = True
    return graph
