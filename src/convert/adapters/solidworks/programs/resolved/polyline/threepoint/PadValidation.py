from __future__ import annotations

import math as MathLib

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.resolved.polyline.sixpoint.Program import (
    HasPolygonCross,
)


def ValidatePad(PointsMm: tuple[tuple[float, float], ...], DepthMm: float) -> None:
    if len(PointsMm) != 3 or any(len(PointPair) != 2 for PointPair in PointsMm):
        raise SldprtFormatError("three-line polyline requires exactly three vertices")
    PointValues = tuple(
        Coordinate for PointPair in PointsMm for Coordinate in PointPair
    )
    if not all(MathLib.isfinite(ValueItem) for ValueItem in PointValues):
        raise SldprtFormatError("three-line vertices must be finite")
    if len(set(PointsMm)) != 3:
        raise SldprtFormatError("three-line vertices must be unique")
    if HasPolygonCross(PointsMm):
        raise SldprtFormatError("three-line edges must not intersect")
    AreaTwice = sum(
        PointsMm[IndexPos][0] * PointsMm[(IndexPos + 1) % 3][1]
        - PointsMm[(IndexPos + 1) % 3][0] * PointsMm[IndexPos][1]
        for IndexPos in range(3)
    )
    if AreaTwice == 0.0:
        raise SldprtFormatError("three-line area must be nonzero")
    if not MathLib.isfinite(DepthMm) or DepthMm <= 0.0:
        raise SldprtFormatError("three-line depth must be finite and positive")
