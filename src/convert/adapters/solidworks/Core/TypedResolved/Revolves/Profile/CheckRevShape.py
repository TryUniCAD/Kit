from collections.abc import Mapping
from math import isclose as IsClose

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment


# measured rectangular sweeps must not silently admit crossing axes arbitrary contours or inconsistent solver directions
def CheckRevShape(
    PointsValue: Mapping[int, LinePoint],
    LinesValue: tuple[LineSegment, ...],
    AxisPoints: Mapping[int, LinePoint],
    AxisValue: LineSegment,
    RulesValue: tuple[LineAxis, ...],
) -> None:
    StartValue, EndValue = (
        AxisPoints[IndexValue].PositionValue
        for IndexValue in (AxisValue.StartValue, AxisValue.EndValue)
    )
    if (
        not IsClose(StartValue[0], EndValue[0], abs_tol=1e-10)
        or EndValue[1] <= StartValue[1]
        or (
            min(PointValue.PositionValue[0] for PointValue in PointsValue.values())
            <= StartValue[0]
        )
    ):
        raise ValueError(
            "ordinary revolve requires an upward construction axis left of its contour"
        )
    AxisValues = {PointValue.PositionValue[0] for PointValue in PointsValue.values()}
    OtherValues = {PointValue.PositionValue[1] for PointValue in PointsValue.values()}
    if (
        len(AxisValues) != 2
        or len(OtherValues) != 2
        or {PointValue.PositionValue for PointValue in PointsValue.values()}
        != {
            (FirstValue, SecondValue)
            for FirstValue in AxisValues
            for SecondValue in OtherValues
        }
    ):
        raise ValueError(
            "ordinary revolve rectangular contour is outside measured semantics"
        )
    for RuleValue in RulesValue:
        LineValue = next(
            LineValue
            for LineValue in LinesValue
            if LineValue.IndexValue == RuleValue.LineValue
        )
        CoordIndex = 1 if RuleValue.CodeValue == 4 else 0
        if not IsClose(
            PointsValue[LineValue.StartValue].PositionValue[CoordIndex],
            PointsValue[LineValue.EndValue].PositionValue[CoordIndex],
            abs_tol=1e-10,
        ):
            raise ValueError(
                "ordinary revolve unary relation disagrees with actual contour coordinates"
            )
