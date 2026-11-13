from __future__ import annotations

import math as MathLib

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.resolved.polyline.sixpoint.Program import (
    HasPolygonCross,
)


def ValidatePad(PointsMm: tuple[tuple[float, float], ...], DepthMm: float) -> None:
    if len(PointsMm) != 5 or any(len(PointPair) != 2 for PointPair in PointsMm):
        raise SldprtFormatError("five-line polyline requires exactly five vertices")
    PointValues = tuple(
        Coordinate for PointPair in PointsMm for Coordinate in PointPair
    )
    if not all(MathLib.isfinite(ValueItem) for ValueItem in PointValues):
        raise SldprtFormatError("five-line vertices must be finite")
    if len(set(PointsMm)) != len(PointsMm):
        raise SldprtFormatError("five-line vertices must be unique")
    if HasPolygonCross(PointsMm):
        raise SldprtFormatError("five-line edges must not intersect")
    AreaTwice = sum(
        PointsMm[IndexPos][0] * PointsMm[(IndexPos + 1) % 5][1]
        - PointsMm[(IndexPos + 1) % 5][0] * PointsMm[IndexPos][1]
        for IndexPos in range(5)
    )
    if AreaTwice == 0.0:
        raise SldprtFormatError("five-line area must be nonzero")
    if not MathLib.isfinite(DepthMm) or DepthMm <= 0.0:
        raise SldprtFormatError("five-line depth must be finite and positive")
