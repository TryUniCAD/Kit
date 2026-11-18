from copy import deepcopy
from math import fsum, isclose, isfinite

from AuthorCurves import require


PLANE_AXES = {"Right Plane": 0, "Top Plane": 1, "Front Plane": 2}


def driving_request(case):
    mates = [row for row in case["mates"] if row["kind"] == "distance"]
    require(len(mates) == 1, "the controlled edit requires one driving distance")
    return mates[0]


def verify_case(case, fixed, length):
    placements = case["placements"]
    mates = case["mates"]
    require(type(fixed) is int and 0 <= fixed < len(placements)
            and case["fixed_occurrence"] == fixed
            and 2 <= len(placements) <= 32 and 2 <= len(mates) <= 32,
            "the controlled group needs direct placements and one known fixed occurrence")
    require(all(row["axis"] in ("x", "y", "z") and len(row["translation_m"]) == 3
                and all(type(v) in (int, float) and isfinite(v) for v in (*row["translation_m"], row["angle_deg"]))
                for row in placements), "the controlled placements must be finite rigid principal-axis rotations")
    names = set()
    matches = set()
    for row in mates:
        kind = row["kind"]
        require(kind in {"distance", "parallel", "coincident"} and isinstance(row["name"], str)
                and row["name"] and row["name"] not in names
                and len(row["planes"]) == 2, "the controlled mate group has an unsupported kind or name")
        endpoints = []
        for index, plane in row["planes"]:
            require(type(index) is int and 0 <= index < len(placements) and plane in PLANE_AXES,
                    "a controlled mate endpoint must select an actual occurrence and principal plane")
            endpoints.append(index)
        key = kind, frozenset(endpoints)
        require(len(key[1]) == 2 and key not in matches, "the controlled mate must have two identifiable participants")
        names.add(row["name"])
        matches.add(key)
    drive = driving_request(case)
    start = drive["distance_m"]
    require(type(start) in (int, float) and isfinite(start) and start > 0.0
            and type(length) in (int, float) and isfinite(length) and length > 0.0 and length != start
            and fixed in {index for index, _ in drive["planes"]},
            "the edit needs a changed positive driving distance attached to the fixed occurrence")


def dot(first, second):
    return fsum(left * right for left, right in zip(first, second, strict=True))


def measured_relation(row, transforms):
    (left, left_plane), (right, right_plane) = row["planes"]
    first, second = transforms[left], transforms[right]
    axis_first, axis_second = PLANE_AXES[left_plane] * 3, PLANE_AXES[right_plane] * 3
    normal = first[axis_first:axis_first + 3]
    require(isclose(dot(normal, second[axis_second:axis_second + 3]), 1.0, rel_tol=0.0, abs_tol=1e-10),
            f"{row['name']} has misaligned occurrence-plane normals")
    offset = [second[9 + index] - first[9 + index] for index in range(3)]
    return normal, dot(offset, normal)


def check_satisfied(mates, transforms):
    for row in mates:
        _, separation = measured_relation(row, transforms)
        if row["kind"] == "coincident":
            require(isclose(separation, 0.0, rel_tol=0.0, abs_tol=1e-12),
                    "the occurrence placements must retain each coincident plane")
        elif row["kind"] == "distance":
            require(isclose(separation, row["distance_m"], rel_tol=0.0, abs_tol=1e-12),
                    "the signed driving separation must match the occurrence geometry")


def predict_edit(case, length, placement_transform):
    edit = deepcopy(case)
    drive = driving_request(edit)
    left, right = [index for index, _ in drive["planes"]]
    moving = right if left == edit["fixed_occurrence"] else left
    sign = 1 if moving == right else -1
    before = [placement_transform(row) for row in edit["placements"]]
    check_satisfied(edit["mates"], before)
    normal, current = measured_relation(drive, before)
    movement = sign * (length - current)
    edit["placements"][moving]["translation_m"] = [
        origin + movement * direction
        for origin, direction in zip(before[moving][9:12], normal, strict=True)
    ]
    drive["distance_m"] = length
    check_satisfied(edit["mates"], [placement_transform(row) for row in edit["placements"]])
    return edit
