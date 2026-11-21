import math
import re
from itertools import product

SCHEMA = "kit.sw2026.edge-fillet-disclosed-spec.v1"
FIELD_NAMES = {"name", "center_mm", "size_mm", "edge_axis", "corner", "radius_mm", "edit_radius_mm"}
AXES = "xyz"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_cases(spec):
    require(spec.keys() == {"schema", "cohort", "cases"} and spec["schema"] == SCHEMA
            and spec["cohort"] == "disclosed", "the authoring job requires disclosed source intent")
    cases = spec["cases"]
    require(type(cases) is list and len(cases) == 2, "expected exactly two disclosed single-edge cases")
    for case in cases:
        require(case.keys() == FIELD_NAMES and re.fullmatch("[A-Za-z][A-Za-z0-9]{1,47}", case["name"]),
                "unexpected source case data or unsafe name")
        size, center, axis = case["size_mm"], case["center_mm"], case["edge_axis"]
        radii = (case["radius_mm"], case["edit_radius_mm"])
        require(len(size) == 3 and len(center) == 2 and all(type(value) in (int, float) and math.isfinite(value)
                                                            for value in (*size, *center, *radii)),
                "the stock, offset and radii require finite numeric inputs")
        require(all(0.001 <= value <= 300.0 for value in size) and axis in tuple(AXES)
                and case["corner"].keys() == set(AXES) - {axis}
                and all(value in ("min", "max") for value in case["corner"].values()),
                "expected an ordinary bounded rectangular stock and two signed corner sides")
        limit = min(size[index] for index, name in enumerate(AXES) if name != axis)
        require(all(0 < value < limit / 2 for value in radii) and radii[0] != radii[1],
                "both independent radii must stay strictly inside the same convex edge domain")
    first, second = cases
    require(first["name"].casefold() != second["name"].casefold()
            and first["edge_axis"] != second["edge_axis"]
            and first["size_mm"] != second["size_mm"]
            and len({first["radius_mm"], first["edit_radius_mm"], second["radius_mm"], second["edit_radius_mm"]}) == 4,
            "the two disclosed cases must vary stock, selected edge and all requested radii")
    return cases


def stock(case):
    width, height, depth = (value / 1000.0 for value in case["size_mm"])
    cx, cy = (value / 1000.0 for value in case["center_mm"])
    bounds = ((cx - width / 2, cx + width / 2), (cy - height / 2, cy + height / 2), (0.0, depth))
    return (width, height, depth), bounds


def edge_role(case):
    sizes, bounds = stock(case)
    axis = AXES.index(case["edge_axis"])
    transverse = tuple(index for index in range(3) if index != axis)
    side = {index: int(case["corner"][AXES[index]] == "max") for index in transverse}
    endpoint = [bounds[index][side.get(index, 0)] for index in range(3)]
    inward = {index: -1 if side[index] else 1 for index in transverse}
    return sizes[axis], axis, transverse, endpoint, inward


def predict(case, radius_m=0.0):
    sizes, bounds = stock(case)
    width, height, depth = sizes
    length, axis, transverse, corner, inward = edge_role(case)
    opposite = list(corner)
    opposite[axis] = bounds[axis][1]
    before_volume = math.prod(sizes)
    center = [sum(pair) / 2 for pair in bounds]
    area = 2 * (width * height + width * depth + height * depth)
    vertices = [list(point) for point in product(*bounds)]
    result = {"source_edge": [corner, opposite], "edge_axis": axis, "stock_bounds": bounds}
    if not radius_m:
        return result | {"volume": before_volume, "area": area, "com": center,
                         "vertices": vertices, "counts": {"faces": 6, "edges": 12, "vertices": 8}}
    missing_corner = 1.0 - math.pi / 4
    removed_section = missing_corner * radius_m**2
    removed_volume = removed_section * length
    removed_center = list(corner)
    removed_center[axis] = center[axis]
    arc_center = list(corner)
    for index in transverse:
        removed_center[index] += inward[index] * radius_m * (5.0 / 6.0 - math.pi / 4) / missing_corner
        arc_center[index] += inward[index] * radius_m
    volume = before_volume - removed_volume
    area += -2 * removed_section + (math.pi / 2 - 2) * radius_m * length
    centroid = [(a * before_volume - b * removed_volume) / volume
                for a, b in zip(center, removed_center, strict=True)]
    for endpoint in (corner, opposite):
        vertices.remove(endpoint)
        for index in transverse:
            tangent = list(endpoint)
            tangent[index] += inward[index] * radius_m
            vertices.append(tangent)
    return result | {"volume": volume, "area": area, "com": centroid, "vertices": vertices,
                     "radius_m": radius_m, "fillet_axis_origin": arc_center,
                     "removed_volume": removed_volume, "counts": {"faces": 7, "edges": 15, "vertices": 10}}
