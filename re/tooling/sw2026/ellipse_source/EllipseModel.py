import math
import re


SCHEMA = "kit.sw2026.full-ellipse-blind-boss-intent.v1"
CASES = (
    {"name": "EllipseFrontA", "center_mm": [18.25, -6.375], "radii_mm": [21.375, 8.875],
     "angle_deg": 28.75, "depth_mm": 13.125, "edited_depth_mm": 19.375},
    {"name": "EllipseFrontB", "center_mm": [-12.375, 9.125], "radii_mm": [17.625, 11.25],
     "angle_deg": -41.25, "depth_mm": 21.625, "edited_depth_mm": 10.875},
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(spec, cohort):
    require(spec.keys() == {"schema", "cohort", "cases"} and spec["schema"] == SCHEMA
            and spec["cohort"] == cohort and cohort in ("disclosed", "heldout"), "unexpected ellipse source intent")
    cases = spec["cases"]
    require(type(cases) is list and len(cases) == 2, "expected two independent full ellipse cases")
    for case in cases:
        require(case.keys() == CASES[0].keys() and type(case["name"]) is str
                and re.fullmatch("Ellipse[A-Za-z0-9]{1,35}", case["name"]), "unsafe case name or inputs")
        center, radii = case["center_mm"], case["radii_mm"]
        angle, initial, edited = (case[key] for key in ("angle_deg", "depth_mm", "edited_depth_mm"))
        require(type(center) is type(radii) is list and len(center) == len(radii) == 2
                and all(type(value) in (int, float) and math.isfinite(value)
                        for value in (*center, *radii, angle, initial, edited)), "expected finite ellipse inputs")
        major, minor = radii
        require(all(1 <= abs(value) <= 80 for value in center) and 5 <= minor < major <= 55
                and 1.2 <= major / minor <= 3 and 10 <= abs(angle) <= 70 and 3 <= min(initial, edited)
                and max(initial, edited) <= 55 and abs(initial - edited) >= 2,
                "ellipse outside the noncircular, rotated, positive-depth calibration scope")
    first, second = cases
    require(all(first[key] != second[key] for key in first) and first["angle_deg"] > 0 > second["angle_deg"],
            "cases must independently vary all inputs and use opposite angle signs")
    if cohort == "heldout":
        require(all(case[key] not in [public[key] for public in CASES] for case in cases for key in case),
                "private source intent intersects disclosed input")
    return cases


def perimeter(a, b, intervals):
    step = (math.pi / 2) / intervals
    terms = []
    for index in range(intervals + 1):
        angle = index * step
        weight = 1 if index in (0, intervals) else (4 if index % 2 else 2)
        terms.append(weight * math.hypot(a * math.sin(angle), b * math.cos(angle)))
    return 4 * step * math.fsum(terms) / 3


def predict(case):
    x, y = (value / 1000 for value in case["center_mm"])
    a, b = (value / 1000 for value in case["radii_mm"])
    angle = math.radians(case["angle_deg"])
    sine, cosine = math.sin(angle), math.cos(angle)
    width = math.hypot(a * cosine, b * sine)
    height = math.hypot(a * sine, b * cosine)
    cap = math.pi * a * b
    rim = perimeter(a, b, 512)
    require(math.isclose(rim, perimeter(a, b, 1024), rel_tol=2e-13), "ellipse perimeter did not converge")
    states = []
    for key in ("depth_mm", "edited_depth_mm"):
        depth = case[key] / 1000
        states.append({"depth_m": depth, "cap_m2": cap, "side_m2": rim * depth, "volume_m3": cap * depth,
                       "area_m2": 2 * cap + rim * depth, "com_m": [x, y, depth / 2],
                       "bounds_m": [[x - width, x + width], [y - height, y + height], [0.0, depth]]})
    return {"points_m": [[x, y, 0.0], [x + a * cosine, y + a * sine, 0.0],
                         [x - b * sine, y + b * cosine, 0.0]],
            "unit_axes": [[cosine, sine, 0.0], [-sine, cosine, 0.0]],
            "radii_m": [a, b], "rim_m": rim, "states": states}
