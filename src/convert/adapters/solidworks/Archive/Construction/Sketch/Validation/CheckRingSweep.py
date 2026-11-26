from fractions import Fraction

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.CheckVerticals import (
    CheckVerticals,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.InsertSweepMut import (
    InsertSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.MakeSweepEvents import (
    MakeSweepEvents,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.RejectCrossing import (
    RejectCrossing,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.RemoveSweepMut import (
    RemoveSweepMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepNeighbors import (
    AfterSweep,
    BeforeSweep,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.SweepState import (
    SweepState,
)


# scalable exact neighbor checks preserve the published simple polygon validation rule
def CheckRingSweep(PointsValue: tuple[tuple[Fraction, Fraction], ...]) -> None:
    StateValue = SweepState()
    CountValue = len(PointsValue)
    for PositionX, EventValue in sorted(MakeSweepEvents(PointsValue).items()):
        StateValue.PositionX = PositionX
        for EdgeValue in EventValue.StartsValue:
            NodeValue = InsertSweepMut(StateValue, EdgeValue)
            BeforeValue, AfterValue = BeforeSweep(NodeValue), AfterSweep(NodeValue)
            RejectCrossing(
                EdgeValue,
                None if BeforeValue is None else BeforeValue.EdgeValue,
                CountValue,
            )
            RejectCrossing(
                EdgeValue,
                None if AfterValue is None else AfterValue.EdgeValue,
                CountValue,
            )
        CheckVerticals(StateValue, EventValue.VerticalValue, CountValue)
        for EdgeValue in EventValue.EndsValue:
            NodeValue = StateValue.NodesValue[EdgeValue.IndexValue]
            BeforeValue, AfterValue = BeforeSweep(NodeValue), AfterSweep(NodeValue)
            RejectCrossing(
                None if BeforeValue is None else BeforeValue.EdgeValue,
                None if AfterValue is None else AfterValue.EdgeValue,
                CountValue,
            )
            RemoveSweepMut(StateValue, EdgeValue.IndexValue)
