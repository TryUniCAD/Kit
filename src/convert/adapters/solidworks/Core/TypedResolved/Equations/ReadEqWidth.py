from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop


# the dependency must own the actual horizontal side of the anchored rectangle
def ReadEqWidth(LoopValue: LineLoop | None) -> LineDriver:
    if LoopValue is None or LoopValue.DimsValue is None:
        raise ValueError("local width-depth equation requires a fully typed rectangle")
    DimsValue = LoopValue.DimsValue
    OriginValue = DimsValue.OriginValue
    if (
        OriginValue is None
        or OriginValue.PositionValue != (0.0, 0.0)
        or len(DimsValue.DriverValues) != 2
    ):
        raise ValueError(
            "local width-depth equation requires its actual anchored corner"
        )
    WidthValue, HeightValue = DimsValue.DriverValues
    WidthMm, HeightMm = (
        WidthValue.MetresValue / 0.001,
        HeightValue.MetresValue / 0.001,
    )
    PointsValue = LoopValue.PointsValue
    if (
        (WidthValue.NameValue, HeightValue.NameValue) != ("D1", "D2")
        or {Point.PositionValue for Point in PointsValue}
        != {(0.0, 0.0), (WidthMm, 0.0), (0.0, HeightMm), (WidthMm, HeightMm)}
        or {PointsValue[Index].PositionValue for Index in WidthValue.PointValues}
        != {(0.0, 0.0), (WidthMm, 0.0)}
        or {PointsValue[Index].PositionValue for Index in HeightValue.PointValues}
        != {(WidthMm, 0.0), (WidthMm, HeightMm)}
    ):
        raise ValueError(
            "local width-depth equation requires independent width and height"
        )
    return WidthValue
