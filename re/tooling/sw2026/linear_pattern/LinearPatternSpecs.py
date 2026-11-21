from __future__ import annotations

import math
import secrets


CASE_KEYS = {
    "name", "split", "plate_origin_m", "plate_size_m", "plate_depth_m",
    "seed_offset_m", "seed_size_m", "seed_extra_depth_m", "axis_plane",
    "direction_component", "reverse", "spacing_m", "instances",
    "edit_spacing_m", "edit_instances",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(case):
    require(type(case) is dict and case.keys() == CASE_KEYS, "unexpected linear-pattern input fields")
    require(case["split"] in ("disclosed", "heldout"), "unexpected source split")
    require(type(case["name"]) is str and case["name"].isalnum() and 2 <= len(case["name"]) <= 40, "invalid source case name")
    require(case["axis_plane"] in ("Right Plane", "Top Plane"), "direction must be an actual principal reference plane")
    require(case["direction_component"] == (0 if case["axis_plane"] == "Right Plane" else 1), "axis and authored coordinate component disagree")
    require(type(case["reverse"]) is bool, "direction reversal must be an explicit Boolean")
    for key in ("plate_origin_m", "plate_size_m", "seed_offset_m", "seed_size_m"):
        require(type(case[key]) is list and len(case[key]) == 2, "two planar coordinates are required")
        require(all(type(value) in (int, float) and math.isfinite(value) for value in case[key]), "nonfinite planar input")
    for key in ("plate_depth_m", "seed_extra_depth_m", "spacing_m", "edit_spacing_m"):
        require(type(case[key]) in (int, float) and math.isfinite(case[key]) and case[key] > 0, "positive finite lengths are required")
    for key in ("instances", "edit_instances"):
        require(type(case[key]) is int and 2 <= case[key] <= 8, "ordinary count must be an integer from two through eight")
    require(case["spacing_m"] != case["edit_spacing_m"] and case["instances"] != case["edit_instances"], "edits must independently change both driving inputs")
    require(all(value > 0 for value in (*case["plate_size_m"], *case["seed_size_m"])), "positive planar sizes are required")
    axis = case["direction_component"]
    require(min(case["spacing_m"], case["edit_spacing_m"]) > case["seed_size_m"][axis], "pattern copies must remain disjoint")
    travel = (max(case["instances"], case["edit_instances"]) - 1) * max(case["spacing_m"], case["edit_spacing_m"])
    for component in range(2):
        margin = travel if component == axis else 0
        require(0 < case["seed_offset_m"][component] - margin, "seed copies need a strict lower plate margin for either direction")
        require(case["seed_offset_m"][component] + case["seed_size_m"][component] + margin < case["plate_size_m"][component], "seed copies need a strict upper plate margin for either direction")
    return case


def validate_disclosed(value):
    require(value["schema"] == "kit.sw2026.linear-pattern-disclosed-inputs.v2", "unexpected disclosed specification schema")
    cases = value["cases"]
    require(len(cases) == 2 and len({case["name"] for case in cases}) == 2, "two distinct disclosed sources are required")
    require({case["direction_component"] for case in cases} == {0, 1}, "disclosed sources must contrast X and Y")
    for case in cases:
        validate(case)
        require(case["split"] == "disclosed", "disclosed packet contains a non-disclosed source")
    return cases


def heldout_cases():
    random = secrets.SystemRandom()
    result = []
    for index, axis in enumerate(random.sample([0, 1], 2), 1):
        width = random.randrange(51017, 54991) / 100000
        height = random.randrange(55013, 58983) / 100000
        count = random.randrange(5, 7)
        case = {
            "name": f"H{index:02d}", "split": "heldout",
            "plate_origin_m": [random.randrange(-9301, 4703) / 100000, random.randrange(-14701, -3101) / 100000],
            "plate_size_m": [width, height], "plate_depth_m": random.randrange(413, 837) / 100000,
            "seed_offset_m": [width / 2 - 0.004, height / 2 - 0.005],
            "seed_size_m": [random.randrange(613, 991) / 100000, random.randrange(733, 1193) / 100000],
            "seed_extra_depth_m": random.randrange(319, 893) / 100000,
            "axis_plane": "Right Plane" if axis == 0 else "Top Plane", "direction_component": axis,
            "reverse": random.choice([True, False]), "spacing_m": random.randrange(2311, 2701) / 100000,
            "instances": count, "edit_spacing_m": random.randrange(2813, 3091) / 100000,
            "edit_instances": count + 1,
        }
        result.append(validate(case))
    return result


def rectangle(case, seed=False):
    origin = list(case["plate_origin_m"])
    if seed:
        origin = [value + offset for value, offset in zip(origin, case["seed_offset_m"], strict=True)]
    size = case["seed_size_m"] if seed else case["plate_size_m"]
    return {
        "kind": "rectangle", "center_mm": [(origin[axis] + size[axis] / 2) * 1000 for axis in range(2)],
        "width_mm": size[0] * 1000, "height_mm": size[1] * 1000,
    }


def expected(case, spacing, instances, direction):
    validate(case)
    require(type(instances) is int and instances >= 2, "analytical instances must be integral")
    require(len(direction) == 3 and math.isclose(sum(value * value for value in direction), 1.0, abs_tol=1e-10), "a measured unit axis is required")
    require(abs(direction[2]) < 1e-10, "pattern direction leaves the plate sketch plane")
    width, height = case["plate_size_m"]
    seed_width, seed_height = case["seed_size_m"]
    thickness, extra = case["plate_depth_m"], case["seed_extra_depth_m"]
    plate_volume, seed_volume = width * height * thickness, seed_width * seed_height * extra
    origin = case["plate_origin_m"]
    plate_center = [origin[0] + width / 2, origin[1] + height / 2, thickness / 2]
    seed_center = [origin[0] + case["seed_offset_m"][0] + seed_width / 2, origin[1] + case["seed_offset_m"][1] + seed_height / 2, thickness + extra / 2]
    centers = [[seed_center[axis] + index * spacing * direction[axis] for axis in range(3)] for index in range(instances)]
    volume = plate_volume + instances * seed_volume
    com = [(plate_volume * plate_center[axis] + seed_volume * sum(center[axis] for center in centers)) / volume for axis in range(3)]
    area = 2 * width * height + 2 * (width + height) * thickness + instances * 2 * (seed_width + seed_height) * extra
    corners = [[origin[0] + x * width, origin[1] + y * height, z * thickness] for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    for center in centers:
        corners.extend([[center[0] + x * seed_width / 2, center[1] + y * seed_height / 2, thickness + z * extra] for x in (-1, 1) for y in (-1, 1) for z in (0, 1)])
    return {"bodies": 1, "volume": volume, "area": area, "com_sketch": com, "corners_sketch": corners, "seed_centers_sketch": centers}
