from math import dist

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import MakePoint

from PatternAngleGeometry import WITNESS_RADIUS, canonical_angle_geometry, offsets
from PatternHingeGeometry import ORIGIN
from PatternPlaneDirectionRule import cross, dot, unit


ARC_TOLERANCE = 1e-8
LENGTH_TOLERANCE_M = 1e-14
OPEN_ARC_LIMIT_RAD = 3.1415926435898003
INITIAL_TEXT_PARAMETER = 0.5
ARC_CONSTRUCTOR_FLAGS = 0x08 | 0x10


def subtract(left, right):
    return tuple(a - b for a, b in zip(left, right, strict=True))


def point(vector):
    return MakePoint(XValue=vector[0], YValue=vector[1], ZValue=vector[2])


def common_centre(first, second, incoming_first, incoming_second):
    cosine = dot(incoming_first, incoming_second)
    if 1.0 - abs(cosine) < ARC_TOLERANCE:
        raise ValueError("parallel angular witnesses require a different centre branch")
    displacement = subtract(second, first)
    scaled = offsets(ORIGIN, displacement, cosine)
    scale = 1.0 / (1.0 - cosine * cosine)
    first_distance = (dot(displacement, incoming_first) - dot(scaled, incoming_second)) * scale
    return offsets(first, incoming_first, first_distance)


def exterior_side(first_ray, second_ray, direction):
    return dot(cross(first_ray, direction), cross(first_ray, second_ray))


def make_angle_arc_fields(start, finish, angle, *, reverse=False):
    geometry = canonical_angle_geometry(start, finish, angle, reverse=reverse)
    axes = geometry["dimension_basis"]
    shift = geometry["dimension_inverse_shift_m"]
    first, second, anchor = (tuple(dot(world, axis) + delta for axis, delta in zip(axes, shift, strict=True))
                             for world in geometry["witness_points_m"])
    if any(abs(dist(witness, anchor) - WITNESS_RADIUS) > LENGTH_TOLERANCE_M for witness in (first, second)):
        raise ValueError("both ordered witnesses must retain their full length in the dimension frame")
    incoming_first, incoming_second = (unit(subtract(anchor, witness)) for witness in (first, second))
    centre = common_centre(first, second, incoming_first, incoming_second)
    if dist(centre, anchor) > LENGTH_TOLERANCE_M:
        raise ValueError("nonintersecting witnesses are outside the local angular display")
    first_ray, second_ray = (tuple(-axis for axis in incoming) for incoming in (incoming_first, incoming_second))
    if cross(first_ray, second_ray)[2] <= ARC_TOLERANCE:
        raise ValueError("angular arc requires the canonical signed witness order")
    label_point = offsets(ORIGIN, geometry["label_direction"], geometry["label_radius_m"])
    label_offset = subtract(label_point, centre)
    direction = unit(label_offset)
    ordinary_arc = int(angle <= OPEN_ARC_LIMIT_RAD)
    if exterior_side(first_ray, second_ray, direction) >= -ARC_TOLERANCE:
        raise ValueError("ordinary angular arcs require a label exterior to the first witness")
    return {
        "f880": point(direction), "f8a8": -INITIAL_TEXT_PARAMETER, "f8b0": dist(label_offset, ORIGIN),
        "f958": point(first), "f970": point(anchor), "f988": point(second), "f9a0": point(anchor), "f9b8": point(centre),
        "fad0": geometry["ray_separation_m"],
        "f100c": 1, "f1010": 1, "f1008": ordinary_arc,
        "ffb8": point(first_ray), "ffd0": point(second_ray),
        "ffe8": dot(subtract(anchor, centre), first_ray), "fff0": dot(subtract(first, centre), first_ray),
        "fff8": dot(subtract(anchor, centre), second_ray), "f1000": dot(subtract(second, centre), second_ray),
        "f1018": ARC_CONSTRUCTOR_FLAGS,
    }
