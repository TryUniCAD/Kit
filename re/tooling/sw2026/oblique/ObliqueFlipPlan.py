import copy
from math import atan2, cos, isclose, isfinite, pi, sin, sqrt, tan

from ObliqueCylinderPlan import CONTROL, EDITS, NAMES, ORACLE, PRINCIPALS, require

SCHEMA = "kit.sw2026.oblique-cylinder-flip-cases.v1"
BASES = {"angle_a": [1.0, 0.0, 0.0], "angle_b": [0.0, 1.0, 0.0]}
PLANE_NORMALS = {
    "front": [0.0, 0.0, 1.0],
    "top": [0.0, 1.0, 0.0],
    "right": [1.0, 0.0, 0.0],
}
ORDERED_HINGE_PLANES = {
    "hinge_a": ["right", "front"],
    "hinge_b": ["top", "front"],
}


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def cross(first, second):
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def unit(vector):
    length = sqrt(dot(vector, vector))
    require(isfinite(length) and length > 1e-15, "zero or nonfinite direction")
    return [value / length for value in vector]


def hinge(key):
    first, second = ORDERED_HINGE_PLANES[key]
    return unit(cross(PLANE_NORMALS[first], PLANE_NORMALS[second]))


def rotate(vector, axis, angle):
    direction = unit(axis)
    product = cross(direction, vector)
    parallel = dot(direction, vector) * (1.0 - cos(angle))
    return [
        vector[index] * cos(angle)
        + product[index] * sin(angle)
        + direction[index] * parallel
        for index in range(3)
    ]


def cases():
    return [
        {
            "id": "F01",
            "name": "ObliquePositiveFlip",
            "angle_a_rad": 0.2831,
            "angle_b_rad": 0.4367,
            "radius_m": 0.00823,
            "height_m": 0.02637,
            "edit_angle_a_rad": 0.3719,
            "edit_angle_b_rad": 0.2513,
            "edit_radius_m": 0.01019,
            "edit_height_m": 0.03461,
        },
        {
            "id": "F02",
            "name": "ObliqueNegativeFlip",
            "angle_a_rad": -0.3191,
            "angle_b_rad": -0.1973,
            "radius_m": 0.00961,
            "height_m": 0.03289,
            "edit_angle_a_rad": -0.2279,
            "edit_angle_b_rad": -0.4073,
            "edit_radius_m": 0.00787,
            "edit_height_m": 0.02543,
        },
    ]


def validate(case):
    expected = {"id", "name", *EDITS, *("edit_" + name for name in EDITS)}
    require(set(case) == expected, "unexpected independent flip source fields")
    require(
        (case["id"], case["name"])
        in [(value["id"], value["name"]) for value in cases()],
        "only the separately disclosed flip cases are admitted",
    )
    for key in EDITS:
        for name in (key, "edit_" + key):
            value = case[name]
            require(
                type(value) in (int, float) and isfinite(value),
                "nonfinite or nonnumeric source driver",
            )
            require(
                (
                    0.02 < abs(value) < 0.65
                    if key.startswith("angle")
                    else 1e-5 < value < 0.2
                ),
                "driver outside the ordinary acute-angle source profile",
            )
        require(case[key] != case["edit_" + key], "every driver needs a real edit")
        if key.startswith("angle"):
            require(
                case[key] * case["edit_" + key] > 0,
                "this probe does not change flip during a scalar edit",
            )
    return case


def state(case, steps=0):
    validate(case)
    require(type(steps) is int and 0 <= steps <= 4, "invalid source edit step")
    result = {key: case[key] for key in EDITS}
    for key in EDITS[:steps]:
        result[key] = case["edit_" + key]
    return result


def angle_plan(key, value):
    require(key in BASES, "unknown angular owner")
    require(
        type(value) in (int, float) and isfinite(value) and 0.02 < abs(value) < 0.65,
        "angle outside the declared source profile",
    )
    target = (
        [cos(value), 0.0, -sin(value)]
        if key == "angle_a"
        else [0.0, cos(value), -sin(value)]
    )
    direction = hinge("hinge_a" if key == "angle_a" else "hinge_b")
    base = BASES[key]
    signed = atan2(dot(direction, cross(base, target)), dot(base, target))
    require(isclose(abs(signed), abs(value), abs_tol=1e-14), "angle mapping differs")
    reverse = signed < 0.0
    arguments = [16 | (256 if reverse else 0), abs(value), 4, 0.0, 0, 0.0]
    actual = rotate(base, direction, -abs(value) if reverse else abs(value))
    require(
        all(isclose(a, b, abs_tol=1e-14) for a, b in zip(actual, target, strict=True)),
        "independent rotation and desired plane disagree",
    )
    return {
        "base_normal": list(base),
        "directed_hinge": direction,
        "signed_rotation_rad": signed,
        "reverse": reverse,
        "arguments": arguments,
        "normal": target,
        "rodrigues_normal": actual,
    }


def prediction(case, steps=0):
    values = state(case, steps)
    a, b, r, h = (values[key] for key in EDITS)
    dx, dy = h * tan(a), h * tan(b)
    length = sqrt(dx * dx + dy * dy + h * h)
    angles = {
        key: angle_plan(key, values[key + "_rad"]) for key in ("angle_a", "angle_b")
    }
    count = 4096
    interval = 2 * pi / count
    total = 0.0
    for index in range(count + 1):
        theta = index * interval
        value = sqrt(h * h + (dx * cos(theta) + dy * sin(theta)) ** 2)
        total += (1 if index in (0, count) else 4 if index % 2 else 2) * value
    return {
        "drivers": values,
        "body_count": 1,
        "volume_m3": pi * r * r * h,
        "area_m2": 2 * pi * r * r + r * interval * total / 3,
        "com_m": [dx / 2, dy / 2, h / 2],
        "extrusion_displacement_m": [dx, dy, h],
        "axis_unit_positive_z": [dx / length, dy / length, h / length],
        "directed_axis_unit": unit(
            cross(angles["angle_b"]["normal"], angles["angle_a"]["normal"])
        ),
        "angle_plane_normals": {key: value["normal"] for key, value in angles.items()},
        "angle_input_plans": angles,
        "hinge_units": {key: hinge(key) for key in ORDERED_HINGE_PLANES},
        "limit_origin_m": [0.0, 0.0, h],
        "bounds_m": [
            [min(0.0, dx) - r, min(0.0, dy) - r, 0.0],
            [max(0.0, dx) + r, max(0.0, dy) + r, h],
        ],
        "analytic_area_method": "4096-interval composite Simpson rule on an independently parameterized oblique circular extrusion",
    }


def document_plan():
    return {
        "schema": SCHEMA,
        "cases": copy.deepcopy(cases()),
        "units": {"length": "metre", "angle": "radian"},
        "actual_feature_names": copy.deepcopy(NAMES),
        "principal_feature_names": copy.deepcopy(PRINCIPALS),
        "ordered_native_hinge_planes": copy.deepcopy(ORDERED_HINGE_PLANES),
        "construction": "actual ordered plane intersections, one angular plane on each real hinge, selected intersection axis and independent positive-height limit plane",
        "source_history": "two actual angular drivers, one radius driver, one limit-plane distance driver",
        "native_hinge_order_status": "observed in the disclosed predecessor D01, checked directly in every new phase; public selection-to-owner reversal is not statically generalized",
        "original_expectations_rewritten": False,
        "heldout_inputs": [],
    }


def boss_arguments(case):
    validate(case)
    return [
        True,
        False,
        False,
        4,
        0,
        case["height_m"],
        0.0,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        0,
        0.0,
        False,
    ]
