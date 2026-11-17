from __future__ import annotations

import math
import os
import re
import secrets

from AuthorCurves import require


SCHEMA = "kit.sw2026.offset-reference-plane-source.v1"
NORMALS = {"front": (0.0, 0.0, 1.0), "top": (0.0, 1.0, 0.0), "right": (1.0, 0.0, 0.0)}
BASE_NAMES = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}
PLANE, SKETCH, BOSS = "OffsetPlane", "PlaneSketch", "PlaneBoss"
SLOT_IDS = ("D01", "D02", "D03", "D04", "H01", "H02")


def validate_case(case):
    require(set(case) == {"id", "name", "split", "kind", "base", "reverse", "distance_m", "radius_m", "depth_m", "edit_distance_m"}, "unexpected plane source fields")
    require(case["id"] in SLOT_IDS and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,47}", case["name"]) and case["kind"] == "offset" and
            case["base"] in NORMALS and type(case["reverse"]) is bool and case["split"] == ("heldout" if case["id"].startswith("H") else "discovery"),
            "unsupported source profile or slot")
    values = [case[key] for key in ("distance_m", "radius_m", "depth_m", "edit_distance_m")]
    require(all(type(value) in (float, int) and math.isfinite(value) and value > 1e-6 for value in values) and
            case["edit_distance_m"] != case["distance_m"], "plane sources require positive finite distinct driving values")
    return case


def disclosed_cases():
    first = {"name": "FrontOffsetCircle", "split": "discovery", "kind": "offset", "base": "front", "reverse": False,
             "distance_m": 0.01379, "radius_m": 0.00831, "depth_m": 0.00647, "edit_distance_m": 0.02453}
    return [validate_case(first | {"id": "D01"}), validate_case(first | {"id": "D02", "name": "FrontOffsetRepeat"}),
            validate_case({"id": "D03", "name": "TopReverseOffset", "split": "discovery", "kind": "offset", "base": "top", "reverse": True,
                           "distance_m": 0.02713, "radius_m": 0.01127, "depth_m": 0.00419, "edit_distance_m": 0.01471}),
            validate_case({"id": "D04", "name": "RightOffsetCircle", "split": "discovery", "kind": "offset", "base": "right", "reverse": False,
                           "distance_m": 0.01937, "radius_m": 0.00743, "depth_m": 0.00911, "edit_distance_m": 0.03163})]


def heldout_cases():
    require(os.name == "nt", "sealed plane source designs are generated only in the private Windows guest")
    result = []
    for ordinal in (1, 2):
        case = {"id": f"H{ordinal:02d}", "name": f"IndependentOffset{ordinal}", "split": "heldout", "kind": "offset",
                "base": secrets.choice(tuple(NORMALS)), "reverse": bool(secrets.randbelow(2)),
                "distance_m": (8000 + secrets.randbelow(27001)) / 1e6, "radius_m": (4000 + secrets.randbelow(11001)) / 1e6,
                "depth_m": (3000 + secrets.randbelow(8001)) / 1e6, "edit_distance_m": (40000 + secrets.randbelow(25001)) / 1e6}
        result.append(validate_case(case))
    return result


def geometry(case, edited=False):
    validate_case(case)
    distance = case["edit_distance_m"] if edited else case["distance_m"]
    radius, depth = case["radius_m"], case["depth_m"]
    normal = NORMALS[case["base"]]
    signed = -distance if case["reverse"] else distance
    origin = [signed * value for value in normal]
    return {"body_count": 1, "volume": math.pi * radius * radius * depth, "area": 2 * math.pi * radius * (radius + depth),
            "com": [origin[index] + normal[index] * depth / 2 for index in range(3)], "plane_origin": origin, "normal": list(normal),
            "distance_m": distance, "radius_m": radius, "depth_m": depth}
