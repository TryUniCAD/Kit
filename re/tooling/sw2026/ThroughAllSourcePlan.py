from __future__ import annotations

from math import acos, isfinite, pi, sqrt
import os
import re
import secrets

from AuthorCurves import require

SCHEMA = "kit.sw2026.through-all-source-cases.v1"
SLOTS = tuple(f"D{index:02d}" for index in range(1, 7)) + tuple(
    f"H{index:02d}" for index in range(1, 5)
)
PLANES = {"front": "Front Plane", "top": "Top Plane", "right": "Right Plane"}
NAMES = ("StockProfile", "StockBoss", "ThroughProfile", "ThroughFeature")


def model_point(plane, local):
    u, v, n = local
    return {"front": [u, v, n], "top": [u, n, -v], "right": [n, v, -u]}[plane]


def validate(case):
    keys = {
        "id",
        "name",
        "split",
        "operation",
        "direction",
        "plane",
        "stock_size_m",
        "stock_center_m",
        "circle_center_m",
        "radius_m",
        "edit_stock_depth_m",
        "api_placeholder_depths_m",
    }
    require(
        set(case) == keys
        and case["id"] in SLOTS
        and case["split"] == ("heldout" if case["id"].startswith("H") else "discovery"),
        "through-all source membership differs",
    )
    require(
        re.fullmatch(r"[A-Za-z][A-Za-z0-9]{4,60}", case["name"])
        and case["operation"] in ("cut", "boss")
        and case["direction"] in ("forward", "reverse", "both")
        and case["plane"] in PLANES,
        "unsupported through-all source identity",
    )
    require(
        len(case["stock_size_m"]) == 3
        and len(case["stock_center_m"])
        == len(case["circle_center_m"])
        == len(case["api_placeholder_depths_m"])
        == 2,
        "source geometry requires complete independently authored coordinates",
    )
    values = [
        *case["stock_size_m"],
        *case["stock_center_m"],
        *case["circle_center_m"],
        case["radius_m"],
        case["edit_stock_depth_m"],
        *case["api_placeholder_depths_m"],
    ]
    require(
        all(type(value) in (int, float) and isfinite(value) for value in values),
        "nonfinite source geometry",
    )
    require(
        all(
            value > 1e-5
            for value in (
                *case["stock_size_m"],
                case["radius_m"],
                case["edit_stock_depth_m"],
                *case["api_placeholder_depths_m"],
            )
        )
        and case["stock_size_m"][2] != case["edit_stock_depth_m"],
        "source dimensions must be positive and editable",
    )
    width, height, _ = case["stock_size_m"]
    x, y = case["stock_center_m"]
    cx, cy = case["circle_center_m"]
    radius = case["radius_m"]
    require(abs(cy - y) + radius < height / 2, "circle crosses a second stock boundary")
    if case["operation"] == "cut":
        require(
            abs(cx - x) + radius < width / 2,
            "cut circle must lie strictly inside the stock section",
        )
    else:
        require(
            0 < x + width / 2 - cx < radius and cx - radius > x - width / 2,
            "boss circle must cross exactly the positive-u stock boundary",
        )
    return case


def make_case(
    identifier,
    operation,
    direction,
    plane,
    size,
    center,
    circle,
    radius,
    edited,
    placeholders,
):
    return validate(
        {
            "id": identifier,
            "name": "ThroughAll" + identifier + operation.title() + direction.title(),
            "split": "heldout" if identifier.startswith("H") else "discovery",
            "operation": operation,
            "direction": direction,
            "plane": plane,
            "stock_size_m": list(size),
            "stock_center_m": list(center),
            "circle_center_m": list(circle),
            "radius_m": radius,
            "edit_stock_depth_m": edited,
            "api_placeholder_depths_m": list(placeholders),
        }
    )


def disclosed_cases():
    return [
        make_case(
            "D01",
            "cut",
            "forward",
            "front",
            (0.0713, 0.0467, 0.02791),
            (0.00317, -0.00239),
            (-0.00673, 0.00419),
            0.00823,
            0.04153,
            (0.00519, 0.00931),
        ),
        make_case(
            "D02",
            "cut",
            "reverse",
            "top",
            (0.0841, 0.0539, 0.03247),
            (-0.00431, 0.00373),
            (0.00719, -0.00583),
            0.00961,
            0.04637,
            (0.00683, 0.01127),
        ),
        make_case(
            "D03",
            "cut",
            "both",
            "right",
            (0.0637, 0.0493, 0.02483),
            (0.00271, -0.00413),
            (-0.00529, 0.00317),
            0.00743,
            0.03871,
            (0.00467, 0.01013),
        ),
        make_case(
            "D04",
            "boss",
            "forward",
            "top",
            (0.0751, 0.0517, 0.02963),
            (0.00419, -0.00311),
            (0.03831, 0.00273),
            0.00937,
            0.04379,
            (0.00583, 0.01241),
        ),
        make_case(
            "D05",
            "boss",
            "reverse",
            "right",
            (0.0689, 0.0473, 0.02671),
            (-0.00329, 0.00217),
            (0.02771, -0.00437),
            0.00871,
            0.03943,
            (0.00731, 0.01317),
        ),
        make_case(
            "D06",
            "boss",
            "both",
            "front",
            (0.0817, 0.0571, 0.03119),
            (0.00283, -0.00271),
            (0.03971, 0.00513),
            0.01019,
            0.04813,
            (0.00617, 0.01429),
        ),
    ]


def geometry(case, edited=False):
    validate(case)
    width, height, original = case["stock_size_m"]
    depth = case["edit_stock_depth_m"] if edited else original
    x, y = case["stock_center_m"]
    cx, cy = case["circle_center_m"]
    radius = case["radius_m"]
    both = case["direction"] == "both"
    span = depth if both else depth / 2
    z = 0.0 if both else (1 if case["direction"] == "forward" else -1) * depth / 4
    base_volume = width * height * depth
    base_area = 2 * (width * height + width * depth + height * depth)
    if case["operation"] == "cut":
        removed = pi * radius * radius * span
        volume = base_volume - removed
        area = (
            base_area
            + 2 * pi * radius * span
            - (2 * pi * radius * radius if both else 0)
        )
        com = [
            (base_volume * a - removed * b) / volume
            for a, b in zip((x, y, 0.0), (cx, cy, z), strict=True)
        ]
        return {
            "analytic_qualified": True,
            "body_count": 1,
            "volume": volume,
            "area": area,
            "com_local": com,
            "com": model_point(case["plane"], com),
            "removed_volume": removed,
            "axial_span_m": span,
        }
    edge = x + width / 2 - cx
    segment = radius * radius * acos(edge / radius) - edge * sqrt(
        radius * radius - edge * edge
    )
    cap_x = cx + (2 / 3) * (radius * radius - edge * edge) ** 1.5 / segment
    added = segment * span
    volume = base_volume + added
    com = [
        (base_volume * a + added * b) / volume
        for a, b in zip((x, y, 0.0), (cap_x, cy, z), strict=True)
    ]
    arc = 2 * radius * acos(edge / radius)
    chord = 2 * sqrt(radius * radius - edge * edge)
    return {
        "analytic_qualified": False,
        "reason": "native finite through-all boss span is not yet independently bound",
        "body_count": 1,
        "unverified_stock_span_hypothesis": {
            "volume": volume,
            "area": base_area + 2 * segment + (arc - chord) * span,
            "com_local": com,
            "com": model_point(case["plane"], com),
            "axial_span_m": span,
        },
        "minimum_volume": base_volume,
        "minimum_area": 0.0,
    }


def heldout_cases():
    require(
        os.name == "nt",
        "new sealed through-all designs are created only inside the guest",
    )

    def length(low, spread):
        return (low + secrets.randbelow(spread)) / 1_000_000

    result = []
    for ordinal, operation in enumerate(("cut", "cut", "boss", "boss"), 1):
        width, height = length(67000, 21000), length(45000, 17000)
        depth, edited = length(21000, 14000), length(42000, 14000)
        center = [length(1000, 5000), -length(1000, 5000)]
        radius = length(6500, 3500)
        circle = (
            [center[0] - length(4000, 5000), center[1] + length(2000, 4000)]
            if operation == "cut"
            else [
                center[0] + width / 2 - radius * length(350, 301) * 1000,
                center[1] + length(1000, 4000),
            ]
        )
        direction = secrets.choice(("forward", "reverse")) if ordinal % 2 else "both"
        result.append(
            make_case(
                f"H{ordinal:02d}",
                operation,
                direction,
                secrets.choice(tuple(PLANES)),
                (width, height, depth),
                center,
                circle,
                radius,
                edited,
                (length(3000, 4000), length(9000, 4000)),
            )
        )
    return result
