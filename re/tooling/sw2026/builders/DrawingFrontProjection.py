from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite

from builders.Assembly import bounding_box
from builders.AssemblyDocument import _child_bounds
from builders.Definition import identity_transform
from builders.DrawingSheet import DrawingSheet
from builders.Part import PartConstruction


def _axes(point):
    return dict(zip("xyz", point, strict=True))


def _translation(point):
    return {**identity_transform(), **dict(zip(("f58", "f60", "f68"), point, strict=True))}


def _rectangular_bounds(child):
    minimum, maximum = _child_bounds(child)
    profile = child.profile
    frame = profile.profile["_frame"]
    corners = tuple((node["pos"]["x"], node["pos"]["y"]) for node in profile.points)
    expected = set(product(*zip(minimum[:2], maximum[:2], strict=True)))
    perimeter = zip(corners, (*corners[1:], corners[0]), strict=True)
    aligned = all((left[0] == right[0]) != (left[1] == right[1]) for left, right in perimeter)
    if (frame.u, frame.v, frame.origin) != ((1, 0, 0), (0, 1, 0), (0, 0, 0)) or profile.line_count != 4 or set(corners) != expected or not aligned:
        raise ValueError("ordinary front-view construction requires an XY-aligned rectangular prism")
    return bounding_box(minimum=minimum, maximum=maximum)


@dataclass(frozen=True, slots=True)
class FrontProjection:
    view: dict
    header_bounds: dict
    sheet_sketch_transform: dict
    model_plane_transform: dict


def front_projection(*, child: PartConstruction, sheet: DrawingSheet, orientation, position, scale):
    if not isinstance(child, PartConstruction) or not isinstance(sheet, DrawingSheet):
        raise ValueError("front projection needs the generated part and the authored paper settings")
    if orientation != "*Front" or type(scale) not in (float, int) or scale != 1:
        raise ValueError("this construction covers the ordinary front orientation at explicit 1:1 view scale")
    if not isinstance(position, (list, tuple)) or len(position) != 2 or any(type(value) not in (float, int) or not isfinite(value) for value in position):
        raise ValueError("front projection requires two finite sheet coordinates")
    model_box = _rectangular_bounds(child)
    center = tuple(model_box[f"b{index}"] for index in range(3))
    origin = (*map(float, position), 0.0)
    translation = tuple(left - right for left, right in zip(origin, center, strict=True))
    half_width, half_height = (model_box[f"b{index + 3}"] - center[index] for index in range(2))
    x, y = origin[:2]
    projected = (x - half_width, y - half_height, x + half_width, y + half_height)
    margin = min(sheet.dimensions) * 0.02
    xmin, ymin, xmax, ymax = tuple(value + delta for value, delta in zip(projected, (-margin, -margin, margin, margin), strict=True))
    header_bounds = bounding_box(minimum=(xmin, ymin, 0.0), maximum=(xmax, ymax, 0.0))
    header_bounds.update(zip(("b0", "b1", "b2"), origin, strict=True))
    view = {"f5e0": _translation(translation), "f778": _axes(origin), "f600": model_box, "has_f648": 1, "f648": _axes(center),
            "f780": 1.0, "f788": 1.0, "f1018": orientation}
    view.update(zip(("f6d8", "f6e0", "f6e8", "f6f0"), (xmin, ymin, xmax, ymax), strict=True))
    view.update(zip(("f718", "f720", "f728", "f730", "f738", "f740", "f748", "f750"), (*projected, *projected), strict=True))
    return FrontProjection(view, header_bounds, _translation(tuple(-value for value in origin)), _translation(tuple(-value for value in center)))
