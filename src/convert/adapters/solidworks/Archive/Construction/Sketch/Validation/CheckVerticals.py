from fractions import Fraction

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.RejectCrossing import (
    RejectCrossing,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNeighbors import (
    AfterSweep,
    LowerSweep,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepEdge import (
    SweepEdge,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# vertical range checks must detect collinear overlap and contact with every active intersecting ordinate
def CheckVerticals(
    StateValue: SweepState, VerticalValues: list[SweepEdge], CountValue: int
) -> None:
    PreviousValue: SweepEdge | None = None
    for EdgeValue in sorted(VerticalValues, key=VerticalStart):
        if (
            PreviousValue is not None
            and EdgeValue.StartValue[1] <= PreviousValue.EndValue[1]
        ):
            RejectCrossing(PreviousValue, EdgeValue, CountValue)
        if PreviousValue is None or EdgeValue.EndValue[1] > PreviousValue.EndValue[1]:
            PreviousValue = EdgeValue
        NodeValue = LowerSweep(StateValue, EdgeValue.StartValue[1])
        while (
            NodeValue is not None
            and NodeValue.EdgeValue.GetOrdinate(StateValue.PositionX)
            <= EdgeValue.EndValue[1]
        ):
            RejectCrossing(EdgeValue, NodeValue.EdgeValue, CountValue)
            NodeValue = AfterSweep(NodeValue)


# vertical ranges use their exact lower endpoint as the deterministic processing order
def VerticalStart(EdgeValue: SweepEdge) -> Fraction:
    return EdgeValue.StartValue[1]
