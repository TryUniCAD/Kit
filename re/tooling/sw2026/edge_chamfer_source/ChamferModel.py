import math
import re
from itertools import product

from FilletModel import AXES, edge_role, require, stock

SCHEMA = "kit.sw2026.edge-chamfer-source-spec.v1"
FIELDS = {"name", "center_mm", "size_mm", "edge_axis", "corner", "distance_mm", "angle_deg", "edit"}
ROLES = ("distance_mm", "angle_deg")
BRANCHES = tuple(product((0, 1), ("tan", "cot")))


def validate_spec(spec):
    require(spec.keys() == {"schema", "cohort", "cases"} and spec["schema"] == SCHEMA
            and spec["cohort"] in ("disclosed", "heldout"), "unexpected chamfer source spec")
    cases = spec["cases"]
    require(type(cases) is list and len(cases) == 2, "exactly two independently sized single-edge stocks required")
    for case in cases:
        require(case.keys() == FIELDS and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,47}", case["name"]),
                "source case fields or name differ")
        size, center, axis = case["size_mm"], case["center_mm"], case["edge_axis"]
        require(len(size) == 3 and len(center) == 2 and axis in tuple(AXES)
                and case["corner"].keys() == set(AXES) - {axis}
                and all(side in ("min", "max") for side in case["corner"].values()), "unbound stock or edge role")
        require(len(case["edit"]) == 1 and set(case["edit"]) <= set(ROLES), "edit must change one chamfer driver")
        require(all(type(value) in (int, float) and math.isfinite(value)
                    for value in (*size, *center, *(case[k] for k in ROLES), *case["edit"].values())),
                "expected finite independent stock and driver inputs")
        require(all(10 <= value <= 100 for value in size) and all(abs(value) < 70 for value in center),
                "stock outside the disclosed convex chamfer envelope")
        require(all(case[role] != value for role, value in case["edit"].items()), "chamfer edit must change its value")
        sizes, _ = stock(case)
        limit = min(size for index, size in enumerate(sizes) if AXES[index] != axis)
        for edited in (False, True):
            distance, angle = values_si(case, edited)
            require(math.radians(15) <= angle <= math.radians(75) and abs(math.degrees(angle) - 45) >= 4,
                    "choose a nondegenerate angle that separates complementary predictions")
            tangent = math.tan(angle)
            require(0.0005 <= distance and distance * max(tangent, 1 / tangent) < limit * 0.45,
                    "every predicted clip must terminate strictly within the rectangular stock")
    first, second = cases
    require(first["name"].casefold() != second["name"].casefold()
            and first["edge_axis"] != second["edge_axis"] and first["size_mm"] != second["size_mm"]
            and first["distance_mm"] != second["distance_mm"] and first["angle_deg"] != second["angle_deg"]
            and set(first["edit"]) != set(second["edit"]), "cases must vary stock, edge direction and edited driver")
    return cases


def values_si(case, edited):
    values = case | (case["edit"] if edited else {})
    return values["distance_mm"] / 1000, math.radians(values["angle_deg"])


def predict(case, params=None, branch=None):
    sizes, bounds = stock(case)
    length, axis, transverse, first, inward = edge_role(case)
    last = list(first)
    last[axis] = bounds[axis][1]
    corners = [list(point) for point in product(*bounds)]
    stock_volume = math.prod(sizes)
    center = [sum(interval) / 2 for interval in bounds]
    high_a, high_b = (sizes[i] for i in transverse)
    face_areas = [high_a * high_b] * 2 + [length * high_a] * 2 + [length * high_b] * 2
    basic = {"source_edge": [first, last], "stock_bounds": bounds, "edge_axis": axis}
    if params is None:
        return basic | {"vertices": corners, "volume": stock_volume, "area": sum(face_areas), "com": center,
                        "face_areas": sorted(face_areas), "counts": {"faces": 6, "edges": 12, "vertices": 8}}
    distance, angle = params
    side, relation = branch
    tangent = math.tan(angle)
    legs = [distance, distance * (tangent if relation == "tan" else 1 / tangent)]
    if side:
        legs.reverse()
    a, b = legs
    removed_area = a * b / 2
    removed_volume = removed_area * length
    removed_center = list(first)
    removed_center[axis] = center[axis]
    bevel_vertices = []
    for index, leg in zip(transverse, legs, strict=True):
        removed_center[index] += inward[index] * leg / 3
    for endpoint in (first, last):
        corners.remove(endpoint)
        for index, leg in zip(transverse, legs, strict=True):
            point = list(endpoint)
            point[index] += inward[index] * leg
            corners.append(point)
            bevel_vertices.append(point)
    volume = stock_volume - removed_volume
    end_area = high_a * high_b - removed_area
    bevel_area = length * math.hypot(a, b)
    face_areas = [end_area, end_area, length * high_a, length * high_b, length * (high_a - a),
                  length * (high_b - b), bevel_area]
    centroid = [(stock_volume * current - removed_volume * missing) / volume
                for current, missing in zip(center, removed_center, strict=True)]
    return basic | {"vertices": corners, "volume": volume, "area": sum(face_areas), "com": centroid,
                    "face_areas": sorted(face_areas), "bevel_area": bevel_area, "bevel_vertices": bevel_vertices,
                    "legs_m": legs, "counts": {"faces": 7, "edges": 15, "vertices": 10}}


def predictions(cases):
    return [{"name": case["name"], "stock": predict(case),
             "states": {label: [{"branch": list(branch), "geometry": predict(case, values_si(case, edited), branch)}
                                for branch in BRANCHES] for label, edited in (("initial", False), ("edited", True))}}
            for case in cases]
