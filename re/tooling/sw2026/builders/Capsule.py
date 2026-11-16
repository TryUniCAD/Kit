from __future__ import annotations

from math import cos, isfinite, sin

from builders.Circle import arc_node
from builders.Geometry import bind_arrays, bind_permanence
from builders.Sketch import ConstructionError, NodeOrder, PlaneFrame, _bind_local_ref_flag, _vector, new_profile, ordinary_line, ordinary_point


def capsule_profile(*, center_m, radius_m, straight_length_m, rotation_angle_rad, profile, plane, frame):
    if profile.cls != "moProfileFeature_c" or not isinstance(frame, PlaneFrame):
        raise ConstructionError("capsules require an ordinary allocated profile and frame")
    center = _vector(value=center_m, size=2)
    for value in (radius_m, straight_length_m, rotation_angle_rad):
        if type(value) not in (int, float) or not isfinite(value):
            raise ConstructionError("capsule dimensions and rotation must be finite numbers")
    if radius_m <= 0 or straight_length_m <= 0:
        raise ConstructionError("capsules require positive radius and straight length")
    u = (cos(rotation_angle_rad), sin(rotation_angle_rad))
    v = (-u[1], u[0])
    left, right = (_vector(value=(center[i] + sign * straight_length_m * 0.5 * u[i] for i in range(2)), size=2) for sign in (-1, 1))
    positions = tuple(_vector(value=(base[i] + sign * radius_m * v[i] for i in range(2)), size=2) for base, sign in ((left, -1), (right, -1), (right, 1), (left, 1))) + (left, right)
    if len(set(positions)) != 6:
        raise ConstructionError("capsule nodes must remain representably distinct")
    for point in positions:
        frame.world_point(point=point)
    graph = new_profile(profile=profile, plane=plane, frame=frame)
    points = NodeOrder(nodes=tuple(ordinary_point(sketch=graph.sketch, position=point) for point in positions))
    lines = NodeOrder(nodes=tuple(ordinary_line(sketch=graph.sketch, start=points[a], end=points[b], points=points) for a, b in ((0, 1), (2, 3))))
    arcs = NodeOrder(nodes=tuple(arc_node(sketch=graph.sketch, center=points[c], start=points[a], end=points[b], points=points, orientation=1) for a, b, c in ((1, 2, 5), (3, 0, 4))))
    bind_permanence(sketch=graph.sketch, points=points, lines=lines, arcs=arcs)
    bind_arrays(sketch=graph.sketch, points=points, lines=lines, arcs=arcs)
    graph.sketch["_closed_boundary"] = (lines[0], arcs[0], lines[1], arcs[1])
    graph.sketch["_profile_kind"] = "closed_curve"
    _bind_local_ref_flag(sketch=graph.sketch)
    graph.sketch["_requires_update"] = True
    return graph
