from __future__ import annotations

from collections.abc import Sequence
from math import isfinite, sqrt


def bounding_box(*, minimum: Sequence[float], maximum: Sequence[float]) -> dict:
    points = []
    for name, point in (("minimum", minimum), ("maximum", maximum)):
        if not isinstance(point, Sequence) or isinstance(point, (str, bytes, bytearray)) or len(point) != 3:
            raise ValueError(f"{name} must contain three coordinates in model length units")
        if any(type(value) not in (int, float) for value in point):
            raise ValueError(f"{name} coordinates must be real numbers")
        try:
            values = tuple(float(value) for value in point)
        except OverflowError as error:
            raise ValueError(f"{name} coordinates exceed the archive numeric domain") from error
        if not all(isfinite(value) for value in values):
            raise ValueError(f"{name} coordinates must be finite")
        points.append(values)
    low, high = points
    if any(a > b for a, b in zip(low, high, strict=True)):
        raise ValueError("minimum coordinates must not exceed maximum coordinates")
    center = tuple((a + b) * 0.5 for a, b in zip(low, high, strict=True))
    dx, dy, dz = (b - a for a, b in zip(low, high, strict=True))
    radius = sqrt(dx * dx + dy * dy + dz * dz) * 0.5
    values = (*center, *high, *low, radius)
    if not all(isfinite(value) for value in values):
        raise ValueError("derived bounding-box state exceeds the archive numeric domain")
    return {f"b{index}": value for index, value in enumerate(values)}
