from collections.abc import Mapping
from math import dist as Distance
from math import isclose as IsClose

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineAxis import (
    LineAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LinePoint import LinePoint
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.LineEqual import (
    LineEqual,
)


# measured rectangular sweeps must not silently admit crossing axes arbitrary contours or inconsistent solver directions
def CheckRevShape(
    PointsValue: Mapping[int, LinePoint],
    LinesValue: tuple[LineSegment, ...],
    AxisPoints: Mapping[int, LinePoint],
    AxisValue: LineSegment,
    RulesValue: tuple[LineAxis, ...],
    EqualValue: LineEqual | None,
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
    IndexLines = {LineValue.IndexValue: LineValue for LineValue in LinesValue}
    for RuleValue in RulesValue:
        LineValue = IndexLines[RuleValue.LineValue]
        CoordIndex = 1 if RuleValue.CodeValue == 4 else 0
        if not IsClose(
            PointsValue[LineValue.StartValue].PositionValue[CoordIndex],
            PointsValue[LineValue.EndValue].PositionValue[CoordIndex],
            abs_tol=1e-10,
        ):
            raise ValueError(
                "ordinary revolve unary relation disagrees with actual contour coordinates"
            )
    if EqualValue is not None:
        First, Second = (IndexLines[IndexValue] for IndexValue in EqualValue.Indices)
        if {First.StartValue, First.EndValue}.isdisjoint(
            (Second.StartValue, Second.EndValue)
        ) or not IsClose(
            Distance(
                PointsValue[First.StartValue].PositionValue,
                PointsValue[First.EndValue].PositionValue,
            ),
            Distance(
                PointsValue[Second.StartValue].PositionValue,
                PointsValue[Second.EndValue].PositionValue,
            ),
            rel_tol=0.0,
            abs_tol=1e-7,
        ):
            raise ValueError("revolve equal length requires an adjacent square pair")
