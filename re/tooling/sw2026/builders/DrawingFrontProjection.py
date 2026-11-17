from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite

from builders.Assembly import bounding_box
from builders.AssemblyDocument import _child_bounds
from builders.Definition import identity_transform
from builders.DrawingSheet import DrawingSheet
from builders.Part import PartConstruction
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinViewOwners import KViewDirections


def _axes(point):
    return dict(zip("xyz", point, strict=True))


def _frame(point, *, scale=1.0, rotation=None):
    transform = dict(identity_transform() if rotation is None else rotation)
    transform.update(zip(("f58", "f60", "f68"), point, strict=True))
    transform["f70"] = scale
    return transform


def _model_view(child, orientation):
    view, = [row["o"] for row in child.model["f9f8"] if row["o"]["f358"] == orientation]
    rotation = view["f368"]
    if rotation["has_matrix"]:
        basis = rotation["f08"]
        columns = tuple(tuple(basis[f"m{i + 3*j}"] for j in range(3)) for i in range(3))
    else:
        columns = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    return rotation, columns


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
    model_axes: tuple[tuple[float, ...], ...]


def front_projection(*, child: PartConstruction, sheet: DrawingSheet, orientation, position, scale):
    if not isinstance(child, PartConstruction) or not isinstance(sheet, DrawingSheet):
        raise ValueError("view projection needs the generated part and the authored paper settings")
    if not isinstance(orientation, str) or orientation not in KViewDirections:
        raise ValueError("the drawing requires a supported named absolute view")
    if type(scale) not in (float, int) or not isfinite(scale) or scale <= 0 or not isfinite(1.0 / scale):
        raise ValueError("the drawing requires a finite positive explicit view scale")
    if not isinstance(position, (list, tuple)) or len(position) != 2 or any(type(value) not in (float, int) or not isfinite(value) for value in position):
        raise ValueError("view projection requires two finite sheet coordinates")
    model_box = _rectangular_bounds(child)
    center = tuple(model_box[f"b{index}"] for index in range(3))
    origin = (*map(float, position), 0.0)
    rotation, columns = _model_view(child, orientation)
    rotated_center = tuple(sum(value * basis for value, basis in zip(center, axis, strict=True)) for axis in columns)
    geometric_scale = 1.0 if abs(scale - 1.0) <= 1e-8 else float(scale)
    translation = tuple(left - geometric_scale * right for left, right in zip(origin, rotated_center, strict=True))
    half_lengths = tuple(model_box[f"b{index + 3}"] - center[index] for index in range(3))
    half_width, half_height = (
        geometric_scale * sum(length * abs(basis) for length, basis in zip(half_lengths, axis, strict=True))
        for axis in columns[:2]
    )
    x, y = origin[:2]
    projected = (x - half_width, y - half_height, x + half_width, y + half_height)
    margin = min(sheet.dimensions) * 0.02
    xmin, ymin, xmax, ymax = tuple(value + delta for value, delta in zip(projected, (-margin, -margin, margin, margin), strict=True))
    header_bounds = bounding_box(minimum=(xmin, ymin, 0.0), maximum=(xmax, ymax, 0.0))
    header_bounds.update(zip(("b0", "b1", "b2"), origin, strict=True))
    view = {"f5e0": _frame(translation, scale=float(scale), rotation=rotation), "f778": _axes(origin),
            "f600": model_box, "has_f648": 1, "f648": _axes(center),
            "f780": float(scale), "f788": 1.0, "f1010": KViewDirections[orientation], "f1018": orientation}
    view.update(zip(("f6d8", "f6e0", "f6e8", "f6f0"), (xmin, ymin, xmax, ymax), strict=True))
    view.update(zip(("f718", "f720", "f728", "f730", "f738", "f740", "f748", "f750"), (*projected, *projected), strict=True))
    return FrontProjection(
        view, header_bounds, _frame(tuple(-value / scale for value in origin), scale=1.0 / scale),
        _frame(tuple(-value for value in rotated_center), rotation=rotation), columns,
    )
