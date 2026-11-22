from math import isfinite as IsFinite
from typing import cast as CastValue


# native positions require finite numeric pairs before exact topology validation begins
def ReadRingPoint(PointValue: object) -> tuple[float, float]:
    if type(PointValue) not in (tuple, list):
        raise TypeError("polygon position must be a numeric pair")
    ValuesValue = CastValue(tuple[object, ...] | list[object], PointValue)
    if len(ValuesValue) != 2:
        raise ValueError("polygon position must have exactly two coordinates")
    if any(type(Coordinate) not in (int, float) for Coordinate in ValuesValue):
        raise TypeError("polygon coordinates must be real numeric inputs")
    try:
        FirstValue, SecondValue = (
            float(CastValue(float, Coordinate)) for Coordinate in ValuesValue
        )
    except OverflowError as ErrorInfo:
        raise ValueError(
            "polygon coordinate exceeds the native numeric domain"
        ) from ErrorInfo
    if not IsFinite(FirstValue) or not IsFinite(SecondValue):
        raise ValueError("polygon coordinates must be finite")
    return FirstValue, SecondValue
