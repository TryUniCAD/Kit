from __future__ import annotations

from itertools import product
from math import cos, sin


def rotation(orientation):
    if orientation == "*Front":
        return [1., 0., 0., 0., 1., 0., 0., 0., 1.]
    angle = 1.5707963267949001
    if orientation == "*Top":
        return [1., 0., 0., 0., cos(angle), sin(angle), 0., -sin(angle), cos(angle)]
    if orientation == "*Right":
        return [cos(angle), 0., sin(angle), 0., 1., 0., -sin(angle), 0., cos(angle)]
    raise ValueError("origin lifecycle admits only its disclosed principal view families")


def rotate(matrix, point):
    return [sum(point[index] * matrix[index * 3 + axis] for index in range(3)) for axis in range(3)]


def dimensions(case, edited):
    result = dict(case["part"])
    if edited:
        result[case["edit"]["field"]] = case["edit"]["value_m"]
    return result


def vertices(case, edited):
    part = dimensions(case, edited)
    width, height = part["width_m"], part["height_m"]
    left, bottom = (0., 0.) if case["kind"] == "corner" else (-width / 2, -height / 2)
    return [(left, bottom), (left + width, bottom), (left + width, bottom + height), (left, bottom + height)]


def predict(case, edited=False, moved=False):
    part, points = dimensions(case, edited), vertices(case, edited)
    width, height, depth = (part[name] for name in ("width_m", "height_m", "depth_m"))
    xs, ys = zip(*points, strict=True)
    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, depth / 2]
    original_x, original_y = zip(*vertices(case, False), strict=True)
    frame_center = [(min(original_x) + max(original_x)) / 2, (min(original_y) + max(original_y)) / 2, case["part"]["depth_m"] / 2]
    matrix = rotation(case["view"]["orientation"])
    scale = case["view"]["scale"]
    position = list(case["view"]["position_m"])
    if moved:
        position = [value + delta for value, delta in zip(position, case["edit"]["view_move_m"], strict=True)]
    translation = [value - scale * transformed for value, transformed in zip([*position, 0.], rotate(matrix, frame_center), strict=True)]
    projected = [[scale * value + offset for value, offset in zip(rotate(matrix, corner), translation, strict=True)]
                 for corner in product((min(xs), max(xs)), (min(ys), max(ys)), (0., depth))]
    margin = min(case["sheet"]["width_m"], case["sheet"]["height_m"]) * .02
    outline = [min(point[0] for point in projected) - margin, min(point[1] for point in projected) - margin,
               max(point[0] for point in projected) + margin, max(point[1] for point in projected) + margin]
    return {"sheet": case["sheet"]["name"], "sheet_properties": [0, 13, *case["sheet"]["scale_ratio"], 0, case["sheet"]["width_m"], case["sheet"]["height_m"], 1],
            "whats_wrong": 0, "view": {"name": case["view"]["name"], "orientation": case["view"]["orientation"],
            "configuration": case["configuration"], "resolved_reference_path": case["paths"]["child"],
            "position_m": position, "scale": scale, "outline_m": outline,
            "model_to_view": [*matrix, *translation, scale, 0., 0., 0.],
            "child_volume_m3": width * height * depth, "child_area_m2": 2 * (width * height + width * depth + height * depth),
            "child_center_m": center}}
