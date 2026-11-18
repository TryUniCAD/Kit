from __future__ import annotations

from copy import deepcopy
from math import cos, fsum, isclose, isfinite, pi, sin, sqrt
import os
import re
import secrets

from AuthorCurves import require


SCHEMA = "kit.sw2026.perpendicular-mate-source-cases.v1"
AXES = {"Right Plane": 0, "Top Plane": 1, "Front Plane": 2}
PARAMETERS = ("D1@Sketch1", "D2@Sketch1", "D1@Boss-Extrude1")
SLOTS = ("D01", "D02", "D03", "H01", "H02")
IDENTITY = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def dot(first, second):
    return fsum(a * b for a, b in zip(first, second, strict=True))


def multiply(first, second):
    return [fsum(first[row * 3 + index] * second[index * 3 + column] for index in range(3))
            for row in range(3) for column in range(3)]


def axis_rotation(axis, degrees):
    length = sqrt(dot(axis, axis))
    require(length > 0.0, "rotation axis must be nonzero")
    x, y, z = [value / length for value in axis]
    angle = degrees * pi / 180
    c, s = cos(angle), sin(angle)
    v = 1 - c
    return [c + x*x*v, x*y*v + z*s, x*z*v - y*s,
            x*y*v - z*s, c + y*y*v, y*z*v + x*s,
            x*z*v + y*s, y*z*v - x*s, c + z*z*v]


def rotation(steps):
    result = list(IDENTITY)
    for axis, degrees in steps:
        require(axis in "xyz" and len(axis) == 1 and type(degrees) in (float, int) and isfinite(degrees),
                "source orientation requires explicit finite principal rotations")
        direction = [float(index == "xyz".index(axis)) for index in range(3)]
        result = multiply(result, axis_rotation(direction, degrees))
    return result


def transform(placement):
    return [*rotation(placement["orientation"]), *placement["translation_m"], 1.0, 0.0, 0.0, 0.0]


def normal(matrix, plane):
    start = AXES[plane] * 3
    return matrix[start:start + 3]


def point(matrix, local):
    return [fsum(local[row] * matrix[row * 3 + column] for row in range(3)) + matrix[9 + column]
            for column in range(3)]


def expected_transforms(case, edited=False):
    result = [transform(placement) for placement in case["placements"]]
    if edited:
        anchor = case["fixed_occurrence"]
        moving = 1 - anchor
        selected = next(plane for index, plane in case["mate"]["planes"] if index == anchor)
        change = axis_rotation(normal(result[anchor], selected), case["edit_rotation_deg"])
        result[moving][:9] = multiply(result[moving][:9], change)
    return result


def orthogonality(case, transforms):
    (first, left), (second, right) = case["mate"]["planes"]
    return dot(normal(transforms[first], left), normal(transforms[second], right))


def geometry(case, edited=False):
    width, height, depth = case["child_size_m"]
    depth = case["edit_depth_m"] if edited else depth
    volume = width * height * depth
    area = 2 * (width * height + width * depth + height * depth)
    center = [0.0, 0.0, depth / 2]
    centers = [point(matrix, center) for matrix in expected_transforms(case, edited)]
    return {"child": {"volume": volume, "area": area, "com": center},
            "assembly": {"volume": 2 * volume, "area": 2 * area,
                         "com": [fsum(row[index] for row in centers) / 2 for index in range(3)]}}


def validate(case):
    keys = {"id", "name", "split", "child_name", "configuration", "fixed_occurrence", "placements", "mate",
            "child_size_m", "edit_depth_m", "edit_rotation_deg"}
    require(set(case) == keys and case["id"] in SLOTS and case["split"] == ("heldout" if case["id"].startswith("H") else "discovery"),
            "source case membership differs")
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9]{4,60}", case["name"]) and case["child_name"] == "PerpendicularDatum"
            and case["configuration"] == "Default" and case["fixed_occurrence"] in (0, 1), "source identity is outside the small ordinary profile")
    require(len(case["placements"]) == 2 and all(set(row) == {"orientation", "translation_m"} and len(row["orientation"]) <= 4
                and len(row["translation_m"]) == 3 and all(type(value) in (float, int) and isfinite(value) for value in row["translation_m"])
                for row in case["placements"]), "the source must own exactly two finite rigid placements")
    mate = case["mate"]
    require(set(mate) == {"kind", "name", "planes", "api_alignment"} and mate["kind"] == "perpendicular"
            and mate["name"] == "Perpendicular1" and mate["api_alignment"] == 0 and len(mate["planes"]) == 2
            and {index for index, _ in mate["planes"]} == {0, 1} and all(plane in AXES for _, plane in mate["planes"]),
            "the source must select two actual occurrence principal planes")
    require(len(case["child_size_m"]) == 3 and all(type(value) in (float, int) and isfinite(value) and value > 0 for value in case["child_size_m"])
            and type(case["edit_depth_m"]) in (float, int) and isfinite(case["edit_depth_m"]) and case["edit_depth_m"] > 0
            and case["edit_depth_m"] != case["child_size_m"][2]
            and type(case["edit_rotation_deg"]) in (float, int) and isfinite(case["edit_rotation_deg"]) and 1 <= abs(case["edit_rotation_deg"]) <= 75,
            "the source requires positive independent dimensions and a nontrivial valid live reorientation")
    for changed in (False, True):
        matrices = expected_transforms(case, changed)
        require(isclose(orthogonality(case, matrices), 0.0, rel_tol=0.0, abs_tol=1e-12), "the independent requested pose is not perpendicular")
        for matrix in matrices:
            rows = [matrix[index:index + 3] for index in (0, 3, 6)]
            require(all(isclose(dot(a, b), float(i == j), rel_tol=0.0, abs_tol=1e-12)
                        for i, a in enumerate(rows) for j, b in enumerate(rows)), "the source orientation is not rigid")
    require(expected_transforms(case) != expected_transforms(case, True), "the live reorientation must change the moving pose")
    return case


def case_value(identifier, name, planes, first, second, size, turn, depth, anchor=0):
    return validate({"id": identifier, "name": name, "split": "heldout" if identifier.startswith("H") else "discovery",
                     "child_name": "PerpendicularDatum", "configuration": "Default", "fixed_occurrence": anchor,
                     "placements": [first, second], "child_size_m": size, "edit_depth_m": depth, "edit_rotation_deg": turn,
                     "mate": {"kind": "perpendicular", "name": "Perpendicular1", "planes": planes, "api_alignment": 0}})


def disclosed_cases():
    return [
        case_value("D01", "PerpendicularFrontTop", [[0, "Front Plane"], [1, "Top Plane"]],
                   {"orientation": [], "translation_m": [0.0, 0.0, 0.0]},
                   {"orientation": [], "translation_m": [0.1237, 0.0181, 0.0269]},
                   [0.0379, 0.0167, 0.0091], 21.7, 0.0143),
        case_value("D02", "PerpendicularTurnedTopRight", [[1, "Right Plane"], [0, "Top Plane"]],
                   {"orientation": [["z", -37.3]], "translation_m": [-0.0137, 0.0241, -0.0067]},
                   {"orientation": [["z", -37.3]], "translation_m": [0.1571, -0.0219, 0.0383]},
                   [0.0487, 0.0239, 0.0127], -32.9, 0.0181, anchor=1),
        case_value("D03", "PerpendicularQuarterTurn", [[0, "Front Plane"], [1, "Front Plane"]],
                   {"orientation": [["x", 19.1], ["z", 28.7]], "translation_m": [0.0071, -0.0193, 0.0119]},
                   {"orientation": [["y", 90.0], ["x", 19.1], ["z", 28.7]], "translation_m": [0.1843, 0.0317, -0.0231]},
                   [0.0293, 0.0211, 0.0067], 43.1, 0.0113),
    ]


def heldout_cases():
    require(os.name == "nt", "sealed perpendicular designs are created only on the guest fixed drive")
    def length(low, span):
        return (low + secrets.randbelow(span)) / 1_000_000

    result = []
    for ordinal in (1, 2):
        common = [["y", secrets.randbelow(1301) / 10 - 65], ["z", secrets.randbelow(1401) / 10 - 70]]
        planes = secrets.choice((("Right Plane", "Top Plane"), ("Top Plane", "Front Plane"), ("Front Plane", "Right Plane")))
        placement = {"orientation": common, "translation_m": [length(8000, 21000), -length(6000, 13000), length(3000, 15000)]}
        peer = deepcopy(placement)
        peer["translation_m"] = [length(145000, 65000), length(24000, 37000), -length(11000, 23000)]
        result.append(case_value(f"H0{ordinal}", f"PerpendicularSealed0{ordinal}", [[0, planes[0]], [1, planes[1]]], placement, peer,
                                 [length(31000, 23000), length(13000, 17000), length(5000, 7000)],
                                 (-1 if ordinal == 2 else 1) * (137 + secrets.randbelow(350)) / 10, length(16000, 9000), anchor=ordinal - 1))
    return result
