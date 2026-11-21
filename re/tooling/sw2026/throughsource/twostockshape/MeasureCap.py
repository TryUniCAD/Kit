from collections import defaultdict
from math import cos, fsum, hypot, isclose, sin

from interchange.brep.Curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface

from ShapeIntent import require, xyz


def dot(left, right):
    return fsum(a * b for a, b in zip(left, right, strict=True))


def difference(left, right):
    return tuple(a - b for a, b in zip(left, right, strict=True))


def cross(left, right):
    x, y, z = left
    a, b, c = right
    return y * c - z * b, z * a - x * c, x * b - y * a


def trim_integrals(edge, curve, backwards, frame):
    basis = xyz(frame.x_axis), xyz(frame.y_axis)
    if type(curve) is LineCurve:
        center, first, second = xyz(curve.origin), xyz(curve.direction), (0, 0, 0)
    elif type(curve) is CircleCurve:
        center = xyz(curve.center)
        first = tuple(value * curve.radius for value in xyz(curve.reference_direction))
        second = cross(xyz(curve.axis), first)
    else:
        raise ValueError("cap measurement requires its actual line or circle carriers")
    origin = tuple(dot(difference(center, xyz(frame.origin)), axis) for axis in basis)
    local_u = tuple(dot(first, axis) for axis in basis)
    local_v = tuple(dot(second, axis) for axis in basis)
    lower, upper = edge.start_parameter, edge.end_parameter
    if backwards:
        lower, upper = upper, lower
    steps = 2 if type(curve) is LineCurve else 1024
    delta = (upper - lower) / steps
    samples = []
    for index in range(steps + 1):
        param = lower + index * delta
        if type(curve) is LineCurve:
            offset = tuple(value * param for value in local_u)
            dx, dy = local_u
        else:
            cosine, sine = cos(param), sin(param)
            offset = tuple(
                a * cosine + b * sine for a, b in zip(local_u, local_v, strict=True)
            )
            dx, dy = (
                -a * sine + b * cosine for a, b in zip(local_u, local_v, strict=True)
            )
        x, y = (start + value for start, value in zip(origin, offset, strict=True))
        weight = 1 if index in (0, steps) else (4 if index % 2 else 2)
        samples.append(
            tuple(
                weight * value
                for value in (
                    (x * dy - y * dx) / 2,
                    x * x * dy / 2,
                    -y * y * dx / 2,
                    hypot(dx, dy),
                )
            )
        )
    increments = tuple(
        fsum(values) * delta / 3 for values in zip(*samples, strict=True)
    )
    return *increments[:3], abs(increments[3])


def topology_measure(solid, stock):
    brep = solid.brep
    axes = xyz(stock.frame.z_axis)
    lower, upper = stock.extent
    surfaces = {surface.id: surface for surface in brep.surfaces}
    caps = tuple(
        face
        for face in brep.faces
        for surface in (surfaces[face.surface_id],)
        if type(surface) is PlaneSurface
        and isclose(abs(dot(xyz(surface.normal), axes)), 1, rel_tol=0, abs_tol=1e-9)
        and isclose(
            dot(difference(xyz(surface.origin), xyz(stock.frame.origin)), axes),
            upper,
            rel_tol=0,
            abs_tol=1e-9,
        )
    )
    require(len(caps) == 1, "computed B-rep needs one auditable upper cap")
    (top,) = caps
    coedges = {coedge.id: coedge for coedge in brep.coedges}
    loops = {loop.id: loop for loop in brep.loops}
    edges = {edge.id: edge for edge in brep.edges}
    curves = {curve.id: curve for curve in brep.curves}
    integral = []
    for loop_id in top.loop_ids:
        for use_id in loops[loop_id].coedge_ids:
            use = coedges[use_id]
            edge = edges[use.edge_id]
            integral.append(
                trim_integrals(edge, curves[edge.curve_id], use.reversed, stock.frame)
            )
    area, moment_x, moment_y, perimeter = (
        fsum(values) for values in zip(*integral, strict=True)
    )
    require(
        abs(area) > 0 and perimeter > 0, "cap integrals require material and boundary"
    )
    x, y, z = moment_x / area, moment_y / area, (lower + upper) / 2
    centroid = tuple(
        origin + x * u + y * v + z * w
        for origin, u, v, w in zip(
            xyz(stock.frame.origin),
            xyz(stock.frame.x_axis),
            xyz(stock.frame.y_axis),
            axes,
            strict=True,
        )
    )
    edge_uses = defaultdict(list)
    for use in brep.coedges:
        edge_uses[use.edge_id].append(use.reversed)
    require(
        set(edge_uses) == set(edges)
        and all(sorted(value) == [False, True] for value in edge_uses.values()),
        "computed B-rep has a nonmanifold edge or inconsistent winding",
    )
    euler = (
        len(brep.vertices)
        - len(edges)
        + sum(2 - len(face.loop_ids) for face in brep.faces)
    )
    height = upper - lower
    return abs(area) * height, 2 * abs(area) + height * perimeter, centroid, euler
