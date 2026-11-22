from collections.abc import Sequence
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    KStockBounds,
)

# the measured front profile requires a finite separation on every axis
KStockMinSpan = 1e-7


# a box accepted by the rectangle constructor must have two ordered finite corners
def ReadStockBox(BoundsValue: object) -> KStockBounds:
    if not isinstance(BoundsValue, (list, tuple)):
        raise ValueError("expected a finite positive size box in model coordinates")
    Corners = CastValue(Sequence[object], BoundsValue)
    if len(Corners) != 2 or any(
        not isinstance(Corner, (list, tuple))
        or len(CastValue(Sequence[object], Corner)) != 3
        for Corner in Corners
    ):
        raise ValueError("expected a finite positive size box in model coordinates")
    LowerPoint, UpperPoint = CastValue(KStockBounds, Corners)
    try:
        FiniteBox = all(
            type(Value) in (int, float) and IsFinite(Value)
            for Value in (*LowerPoint, *UpperPoint)
        ) and all(
            Upper - Lower > KStockMinSpan and IsFinite(Upper - Lower)
            for Lower, Upper in zip(LowerPoint, UpperPoint, strict=True)
        )
    except OverflowError as ErrorValue:
        raise ValueError(
            "expected a finite positive size box in model coordinates"
        ) from ErrorValue
    if not FiniteBox:
        raise ValueError("expected a finite positive size box in model coordinates")
    return (
        (LowerPoint[0], LowerPoint[1], LowerPoint[2]),
        (UpperPoint[0], UpperPoint[1], UpperPoint[2]),
    )
