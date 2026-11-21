from math import pi as HalfTurn, tau as FullTurn

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)


# the measured part requires a rectangular meridian entirely on the positive side of the selected axis
def ReadAnnularBounds(PlanValue: RevolvePlan) -> tuple[float, float, float, float]:
    Vertices = PlanValue.VerticesValue
    Axial = sorted({Y for _, Y in Vertices})
    XValues = sorted({X for X, _ in Vertices})
    if (
        len(Vertices) != 4
        or len(Axial) != 2
        or len(XValues) != 2
        or set(Vertices) != {(X, Y) for X in XValues for Y in Axial}
        or any(
            A[0] != B[0] and A[1] != B[1]
            for A, B in zip(Vertices, (*Vertices[1:], Vertices[0]), strict=True)
        )
    ):
        raise ValueError("selected revolve requires a rectangular meridian")
    Axis = PlanValue.AxisStart[0]
    return XValues[0] - Axis, XValues[1] - Axis, Axial[0], Axial[1]


# the measured body scope requires disjoint full stocks and a partial cutter opening one wall of each
def CheckSelectedRevolveBands(
    First: RevolvePlan, Second: RevolvePlan, Cut: RevolvePlan
) -> None:
    Frame = (First.AxisValue, First.AxisStart, First.AxisEnd)
    if (
        First.IsReverse
        or Second.IsReverse
        or First.AngleValue != FullTurn
        or Second.AngleValue != FullTurn
        or not 0 < Cut.AngleValue < HalfTurn
        or any(
            (Value.AxisValue, Value.AxisStart, Value.AxisEnd) != Frame
            or Value.EqualRule is not None
            or Value.SideMode != "one_sided"
            or Value.AgainstAngle is not None
            or Value.ThinWalls is not None
            for Value in (First, Second, Cut)
        )
    ):
        raise ValueError(
            "selected revolve requires coaxial full stocks and one partial end"
        )
    InnerLow, InnerHigh, StockLow, StockHigh = ReadAnnularBounds(First)
    OuterLow, OuterHigh, OtherLow, OtherHigh = ReadAnnularBounds(Second)
    CutLow, CutHigh, ToolLow, ToolHigh = ReadAnnularBounds(Cut)
    if (
        not 0 < InnerLow < CutLow < InnerHigh < OuterLow < CutHigh < OuterHigh
        or (StockLow, StockHigh) != (OtherLow, OtherHigh)
        or not StockLow < ToolLow < ToolHigh < StockHigh
    ):
        raise ValueError(
            "selected revolve cutter extends beyond the measured wall profile"
        )
