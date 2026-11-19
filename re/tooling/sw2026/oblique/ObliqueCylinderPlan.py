import copy
from math import cos, isfinite, pi, sin, sqrt, tan

SCHEMA = "kit.sw2026.oblique-cylinder-source-cases.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
NAMES = {
    "hinge_a": "TiltHingeA",
    "hinge_b": "TiltHingeB",
    "angle_a": "TiltPlaneA",
    "angle_b": "TiltPlaneB",
    "direction": "CylinderDirection",
    "limit": "HeightLimit",
    "sketch": "CylinderSketch",
    "boss": "ObliqueCylinder",
}
PRINCIPALS = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}
EDITS = ("angle_a_rad", "angle_b_rad", "radius_m", "height_m")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cases():
    return [
        {
            "id": "D01",
            "name": "ObliqueCircleA",
            "angle_a_rad": 0.2173,
            "angle_b_rad": 0.4879,
            "radius_m": 0.00743,
            "height_m": 0.02371,
            "edit_angle_a_rad": 0.3497,
            "edit_angle_b_rad": 0.2981,
            "edit_radius_m": 0.00917,
            "edit_height_m": 0.03143,
        },
        {
            "id": "D02",
            "name": "ObliqueCircleB",
            "angle_a_rad": 0.3911,
            "angle_b_rad": -0.1637,
            "radius_m": 0.01027,
            "height_m": 0.03619,
            "edit_angle_a_rad": 0.2719,
            "edit_angle_b_rad": -0.3193,
            "edit_radius_m": 0.00869,
            "edit_height_m": 0.02837,
        },
    ]


def validate(case):
    expected = {"id", "name", *EDITS, *("edit_" + name for name in EDITS)}
    require(set(case) == expected, "unexpected disclosed oblique source fields")
    require(
        case["id"] in ("D01", "D02")
        and case["name"] in ("ObliqueCircleA", "ObliqueCircleB"),
        "only disclosed cases are admitted",
    )
    for key in EDITS:
        for name in (key, "edit_" + key):
            value = case[name]
            require(
                type(value) in (int, float) and isfinite(value),
                "nonfinite or nonnumeric oblique driver",
            )
            require(
                (
                    0.02 < abs(value) < 0.65
                    if key.startswith("angle")
                    else 1e-5 < value < 0.2
                ),
                "driver outside ordinary oblique source profile",
            )
        require(
            case[key] != case["edit_" + key],
            "every source driver must have an independent edit",
        )
    return case


def state(case, steps=0):
    validate(case)
    require(type(steps) is int and 0 <= steps <= 4, "invalid source edit step")
    result = {key: case[key] for key in EDITS}
    for key in EDITS[:steps]:
        result[key] = case["edit_" + key]
    return result


def prediction(case, steps=0):
    values = state(case, steps)
    a, b, r, h = (values[key] for key in EDITS)
    dx, dy = h * tan(a), h * tan(b)
    distance = sqrt(dx * dx + dy * dy + h * h)
    count = 4096
    interval = 2 * pi / count
    total = 0.0
    for index in range(count + 1):
        theta = index * interval
        value = sqrt(h * h + (dx * cos(theta) + dy * sin(theta)) ** 2)
        total += (1 if index in (0, count) else 4 if index % 2 else 2) * value
    area = 2 * pi * r * r + r * interval * total / 3
    return {
        "drivers": values,
        "body_count": 1,
        "volume_m3": pi * r * r * h,
        "area_m2": area,
        "com_m": [dx / 2, dy / 2, h / 2],
        "extrusion_displacement_m": [dx, dy, h],
        "axis_unit_positive_z": [dx / distance, dy / distance, h / distance],
        "angle_plane_normals": {
            "angle_a": [cos(a), 0.0, -sin(a)],
            "angle_b": [0.0, cos(b), -sin(b)],
        },
        "limit_origin_m": [0.0, 0.0, h],
        "bounds_m": [
            [min(0.0, dx) - r, min(0.0, dy) - r, 0.0],
            [max(0.0, dx) + r, max(0.0, dy) + r, h],
        ],
        "analytic_area_method": "4096-interval composite Simpson rule on independently parameterized oblique circular extrusion",
    }


def angle_arguments(value):
    require(
        isfinite(value) and 0.02 < abs(value) < 0.65, "angle outside source profile"
    )
    return [16 | (256 if value < 0 else 0), abs(value), 4, 0.0, 0, 0.0]


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


def document_plan():
    return {
        "schema": SCHEMA,
        "cases": [validate(copy.deepcopy(case)) for case in cases()],
        "names": NAMES,
        "principal_names": PRINCIPALS,
        "angle_plane_selection_marks": [0, 1],
        "axis_intersection_selection_marks": [0, 0],
        "extrusion_selection_marks": {
            "profile": 0,
            "end_plane": 1,
            "direction_axis": 16,
        },
        "selected_end_type": 4,
        "length_driver": "D1@HeightLimit",
        "inactive_boss_distance_owner_is_not_a_driving_length": True,
        "writer_output_count": 0,
        "heldout_input_enabled": False,
    }
