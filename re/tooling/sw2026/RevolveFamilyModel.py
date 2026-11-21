from itertools import product
from math import cos, isfinite, pi, radians, sin, tau
import re


SPEC_SCHEMA = "kit.sw2026.revolve-family-models.v1"
WALL_TYPES = {
    "one": "swThinWallOneDirection",
    "opposite": "swThinWallOppDirection",
    "midplane": "swThinWallMidPlane",
    "two": "swThinWallTwoDirection",
}
STOCK_NAMES = ("InnerRevolveStock", "OuterRevolveStock")
FEATURE_NAMES = {"thin": "ThinBossRevolve", "cut": "OrdinaryRevolveCut"}
PROFILE = "RevolveSketch"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def scalar(value):
    need(type(value) in (int, float) and isfinite(value), "expected a finite model scalar")
    return value


def pair(values):
    need(isinstance(values, list) and len(values) == 2, "expected a pair of model scalars")
    return tuple(scalar(value) for value in values)


def validate_specs(spec):
    need(set(spec) == {"schema", "family", "split", "cases"} and spec["schema"] == SPEC_SCHEMA,
         "invalid revolve family specification")
    family, split, cases = spec["family"], spec["split"], spec["cases"]
    need(family in FEATURE_NAMES and split in ("discovery", "heldout"), "invalid revolve family or split")
    need(type(cases) is list and 2 <= len(cases) <= 6, "use 2 to 6 independently authored cases per batch")
    names = set()
    for case in cases:
        base = {"name", "plane", "axis_x_m", "axis_axial_m", "axial_m", "angle_deg", "edit_angle_deg", "reverse"}
        extra = ({"profile_radius_m", "wall_mode", "wall_m", "edit_wall_m", "first_wall_sign"}
                 if family == "thin" else {"radius_m", "stock_radii_m", "stock_axial_m", "scope"})
        need(type(case) is dict and set(case) == base | extra, "case has absent or unknown model properties")
        name = case["name"]
        need(type(name) is str and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,39}", name) and name not in names,
             "invalid or duplicate case name")
        names.add(name)
        need(case["plane"] in ("front", "top", "right") and type(case["reverse"]) is bool, "invalid support or reverse flag")
        scalar(case["axis_x_m"])
        bottom, top = pair(case["axis_axial_m"])
        low, high = pair(case["axial_m"])
        need(bottom < low < high < top, "axis endpoints must enclose the two profile levels")
        angle, edited = scalar(case["angle_deg"]), scalar(case["edit_angle_deg"])
        need(0 < angle < 180 and 0 < edited < 180 and angle != edited, "distinct partial angles below a half turn required")
        if family == "thin":
            validate_thin(case, split)
        else:
            validate_cut(case, bottom, top)
    if split == "heldout":
        need(len(cases) >= 2, "a held-out source batch needs independent geometries")
        signatures = {thin_signature(case) if family == "thin" else cut_signature(case) for case in cases}
        need(len(signatures) == len(cases), "held-out cases must differ in geometric sizes")
    return [dict(case, family=family, split=split) for case in cases]


def thin_signature(case):
    return case["profile_radius_m"], tuple(case["axial_m"]), tuple(case["wall_m"]), case["angle_deg"]


def cut_signature(case):
    return tuple(case["radius_m"]), tuple(case["axial_m"]), tuple(map(tuple, case["stock_radii_m"])), case["angle_deg"]


def validate_thin(case, split):
    mode, sign = case["wall_mode"], case["first_wall_sign"]
    need(mode in WALL_TYPES and (sign is None or type(sign) is int and sign in (-1, 1)), "invalid wall mode or sign")
    need(split != "heldout" or mode == "midplane" or sign in (-1, 1), "held-out asymmetric walls require a predeclared first-wall side")
    original = pair(case["wall_m"])
    edited = pair(case["edit_wall_m"])
    radius = scalar(case["profile_radius_m"])
    for first, second in (original, edited):
        need(0 < first < radius, "first wall must remain clear of the axis")
        if mode == "two":
            need(0 < second < radius and first != second, "two sides need unequal positive walls")
        else:
            need(second == 0, "this wall mode takes one thickness")
    need(original[0] != edited[0] and (mode != "two" or original[1] != edited[1]),
         "each active thickness must have an independent edit")
    need(mode != "two" or edited[0] != original[1], "first edit would obscure second-wall identity")


def validate_cut(case, bottom, top):
    first, second = case["stock_radii_m"]
    first_low, first_high = pair(first)
    second_low, second_high = pair(second)
    cut_low, cut_high = pair(case["radius_m"])
    stock_low, stock_high = pair(case["stock_axial_m"])
    low, high = case["axial_m"]
    need(0 < first_low < cut_low < first_high < second_low < cut_high < second_high,
         "cutter must open the first outer and second inner carriers without joining the stocks")
    need(bottom < stock_low < low < high < stock_high < top, "cutter axial range must remain inside both stocks")
    need(case["scope"] in ("inner", "outer", "all"), "invalid cut owner policy")


def world(case, point):
    x, y, z = point
    return {"front": (x, y, z), "top": (x, z, -y), "right": (z, y, -x)}[case["plane"]]


def polar(case, radius, axial, angle):
    return world(case, (case["axis_x_m"] + radius * cos(angle), axial, -radius * sin(angle)))


def sector(case, radii, axial, angle_deg):
    inner, outer = radii
    low, high = axial
    start, stop = (0.0, radians(angle_deg)) if not case["reverse"] else (-radians(angle_deg), 0.0)
    sweep = stop - start
    height = high - low
    delta = outer**2 - inner**2
    volume = height * sweep * delta / 2
    area = height * sweep * (inner + outer) + sweep * delta
    full = angle_deg == 360
    if not full:
        area += 2 * height * (outer - inner)
    mean_radius = 2 * (outer**3 - inner**3) / (3 * delta)
    offset_x = 0.0 if full else mean_radius * (sin(stop) - sin(start)) / sweep
    offset_z = 0.0 if full else -mean_radius * (cos(start) - cos(stop)) / sweep
    origin = case["axis_x_m"] + offset_x
    center = world(case, (origin, (low + high) / 2, offset_z))
    angles = [start, stop] + [index * pi / 2 for index in range(-4, 5) if start < index * pi / 2 < stop]
    points = tuple(polar(case, *row) for row in product(radii, axial, angles))
    axes = tuple(zip(*points, strict=True))
    return {"volume_m3": volume, "area_m2": area, "com_m": center,
            "bounds_m": tuple(map(min, axes)) + tuple(map(max, axes))}


def thin_predictions(case):
    first, second = case["wall_m"]
    radius = case["profile_radius_m"]
    mode = case["wall_mode"]
    if mode == "midplane":
        bounds = [(None, (radius - first / 2, radius + first / 2))]
    else:
        signs = (case["first_wall_sign"],) if case["first_wall_sign"] is not None else (-1, 1)
        bounds = []
        for sign in signs:
            side = -sign if mode == "opposite" else sign
            bounds.append((sign, tuple(sorted((radius + side * first, radius - side * second)))))
    return [(sign, sector(case, radii, case["axial_m"], case["angle_deg"])) for sign, radii in bounds]


def cut_predictions(case, *, before=False):
    cut_inner, cut_outer = case["radius_m"]
    low, high = case["axial_m"]
    sweep = radians(case["angle_deg"])
    results = {}
    for slot, name, radii in zip(("inner", "outer"), STOCK_NAMES, case["stock_radii_m"], strict=True):
        stock = sector(case, radii, case["stock_axial_m"], 360)
        if before or case["scope"] not in (slot, "all"):
            results[name] = stock | {"cut_face": False}
            continue
        inner, outer = radii
        clipped = (max(inner, cut_inner), min(outer, cut_outer))
        removed = sector(case, clipped, case["axial_m"], case["angle_deg"])
        volume = stock["volume_m3"] - removed["volume_m3"]
        center = tuple((a * stock["volume_m3"] - b * removed["volume_m3"]) / volume
                       for a, b in zip(stock["com_m"], removed["com_m"], strict=True))
        open_radius = outer if slot == "inner" else inner
        results[name] = {
            "volume_m3": volume,
            "area_m2": stock["area_m2"] + removed["area_m2"] - 2 * open_radius * (high - low) * sweep,
            "com_m": center, "bounds_m": stock["bounds_m"], "cut_face": True,
        }
    return results


def edited_case(case):
    result = dict(case, angle_deg=case["edit_angle_deg"])
    if case["family"] == "thin":
        result["wall_m"] = case["edit_wall_m"]
    return result
