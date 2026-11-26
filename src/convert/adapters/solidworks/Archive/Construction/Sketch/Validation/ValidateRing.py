from fractions import Fraction
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.CheckRingSweep import (
    CheckRingSweep,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ReadRingPoint import (
    ReadRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.RingMath import (
    IsOnRingEdge,
    RingTurn,
)


# a native closed ring must reject degeneracy and intersections without altering authored order
def ValidateRing(VerticesValue: object) -> tuple[tuple[float, float], ...]:
    if type(VerticesValue) not in (tuple, list):
        raise TypeError("polygon vertices must be an ordered tuple or list")
    PointsValue = tuple(
        ReadRingPoint(PointValue)
        for PointValue in CastValue(tuple[object, ...] | list[object], VerticesValue)
    )
    CountValue = len(PointsValue)
    if not 3 <= CountValue <= 10_000_000:
        raise ValueError("closed polygon requires three through ten million vertices")
    if len(set(PointsValue)) != CountValue:
        raise ValueError(
            "polygon vertices must be distinct with closure represented by the final edge"
        )
    ExactPoints = tuple(
        (Fraction(PointValue[0]), Fraction(PointValue[1])) for PointValue in PointsValue
    )
    AreaValue = sum(
        PointValue[0] * ExactPoints[(IndexValue + 1) % CountValue][1]
        - ExactPoints[(IndexValue + 1) % CountValue][0] * PointValue[1]
        for IndexValue, PointValue in enumerate(ExactPoints)
    )
    if AreaValue == 0:
        raise ValueError("polygon area must be nonzero")
    for IndexValue, PointValue in enumerate(ExactPoints):
        BeforeValue, AfterValue = (
            ExactPoints[IndexValue - 1],
            ExactPoints[(IndexValue + 1) % CountValue],
        )
        if RingTurn(BeforeValue, PointValue, AfterValue) == 0 and not IsOnRingEdge(
            BeforeValue, AfterValue, PointValue
        ):
            raise ValueError("adjacent polygon edges must not overlap")
    CheckRingSweep(ExactPoints)
    return PointsValue
