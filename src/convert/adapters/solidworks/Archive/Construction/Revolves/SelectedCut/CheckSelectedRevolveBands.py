from math import pi as HalfTurn, tau as FullTurn

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)


# the measured part requires a rectangular meridian entirely on the positive side of the selected axis
def ReadRingBounds(PlanValue: RevolvePlan) -> tuple[float, float, float, float]:
    Vertices = PlanValue.VerticesValue
    Axial = sorted({AxialCoord for _, AxialCoord in Vertices})
    XValues = sorted({RadialCoord for RadialCoord, _ in Vertices})
    if (
        len(Vertices) != 4
        or len(Axial) != 2
        or len(XValues) != 2
        or set(Vertices)
        != {
            (RadialCoord, AxialCoord) for RadialCoord in XValues for AxialCoord in Axial
        }
        or any(
            StartPoint[0] != EndPoint[0] and StartPoint[1] != EndPoint[1]
            for StartPoint, EndPoint in zip(
                Vertices, (*Vertices[1:], Vertices[0]), strict=True
            )
        )
    ):
        raise ValueError("selected revolve requires a rectangular meridian")
    AxisOrigin = PlanValue.AxisStart[0]
    return XValues[0] - AxisOrigin, XValues[1] - AxisOrigin, Axial[0], Axial[1]


# the measured body scope requires disjoint full stocks and a partial cutter opening one wall of each
def CheckCutBands(First: RevolvePlan, Second: RevolvePlan, Cutter: RevolvePlan) -> None:
    Frame = (First.AxisValue, First.AxisStart, First.AxisEnd)
    if (
        First.IsReverse
        or Second.IsReverse
        or First.AngleValue != FullTurn
        or Second.AngleValue != FullTurn
        or not 0 < Cutter.AngleValue < HalfTurn
        or any(
            (Value.AxisValue, Value.AxisStart, Value.AxisEnd) != Frame
            or Value.EqualRule is not None
            or Value.SideMode != "one_sided"
            or Value.AgainstAngle is not None
            or Value.ThinWalls is not None
            for Value in (First, Second, Cutter)
        )
    ):
        raise ValueError(
            "selected revolve requires coaxial full stocks and one partial end"
        )
    InnerLow, InnerHigh, StockLow, StockHigh = ReadRingBounds(First)
    OuterLow, OuterHigh, OtherLow, OtherHigh = ReadRingBounds(Second)
    CutLow, CutHigh, ToolLow, ToolHigh = ReadRingBounds(Cutter)
    if (
        not 0 < InnerLow < CutLow < InnerHigh < OuterLow < CutHigh < OuterHigh
        or (StockLow, StockHigh) != (OtherLow, OtherHigh)
        or not StockLow < ToolLow < ToolHigh < StockHigh
    ):
        raise ValueError(
            "selected revolve cutter extends beyond the measured wall profile"
        )
