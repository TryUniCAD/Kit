from math import cos, dist, isfinite, pi, sin

from PatternHingeGeometry import AXIS, ORIGIN
from PatternPlaneDirectionRule import cross, dot, resolve_local_plane, unit


RIGHT = (1.0, 0.0, 0.0)
WITNESS_RADIUS = 0.001


def offsets(point, vector, distance):
    return tuple(value + axis * distance for value, axis in zip(point, vector, strict=True))


def canonical_angle_geometry(start, finish, angle, *, reverse=False):
    if type(angle) is not float or not 0.0 < angle < pi / 2.0 or reverse is not False:
        raise ValueError("the analytic pattern datum covers an acute unreversed Right plane constraint")
    if (start[:2] != finish[:2] or start[:2] != ORIGIN[:2]
            or not all(isfinite(point[2]) for point in (start, finish)) or not start[2] > 0.0 > finish[2]):
        raise ValueError("an actual directed through-origin negative-Z hinge is required")
    high, low = -finish[2], -start[2]
    length = high - low
    if not isfinite(length) or length <= 1e-7:
        raise ValueError("degenerate hinge sizing is outside the angular datum construction")
    margin = length * 0.05
    borders = (high + margin, low - margin, length + margin, -margin)
    normal = offsets(ORIGIN, RIGHT, cos(angle))
    normal = unit(offsets(normal, cross(AXIS, RIGHT), sin(angle)))
    vertical = unit(cross(normal, AXIS))
    datum_center = resolve_local_plane(ORIGIN, AXIS, normal, borders)["fc8"]
    name_corner = offsets(offsets(ORIGIN, AXIS, borders[1]), vertical, borders[2])
    first_ray = unit(cross(RIGHT, AXIS))
    first = offsets(datum_center, first_ray, WITNESS_RADIUS)
    second = offsets(datum_center, vertical, WITNESS_RADIUS)

    dimension_x = unit(cross(first_ray, AXIS))
    dimension_y = first_ray
    dimension_basis = (dimension_x, dimension_y, AXIS)
    dimension_inverse_shift = tuple(-dot(datum_center, axis) for axis in dimension_basis)
    bisector = unit(offsets(first_ray, vertical, 1.0))
    label = offsets(ORIGIN, bisector, WITNESS_RADIUS)
    label_offset = tuple(a - b for a, b in zip(label, datum_center, strict=True))
    label_delta = (dot(label_offset, dimension_x), dot(label_offset, dimension_y), 0.0)
    return {
        "angle_rad": angle, "root_m": ORIGIN, "basis_u_v_n": (AXIS, vertical, normal),
        "ordered_borders_m": borders, "name_corner_m": name_corner,
        "dimension_basis": dimension_basis, "dimension_inverse_shift_m": dimension_inverse_shift,
        "witness_points_m": (first, second, datum_center), "ray_separation_m": dist(first, second),
        "label_direction": unit(label_delta), "label_radius_m": dist(label_delta, ORIGIN),
    }
