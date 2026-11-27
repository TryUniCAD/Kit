from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from pytest import mark as MarkTests

from convert.adapters.Fusion.Native.Circular.DualFrames.ReadDualFrame import (
    ReadDualFrame,
)
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import (
    CheckDualLive,
)
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample


# archived discovery and sealed holdouts retain the original complete world geometry after qualified comparison
@MarkTests.parametrize(
    "Sample",
    tuple(Value for Value in ReadDualCases() if Value.Frame.z_axis.y == 1.0),
    ids=tuple(
        Value.Identity for Value in ReadDualCases() if Value.Frame.z_axis.y == 1.0
    ),
)
def CheckFrameSaved(Sample: DualCase) -> None:
    Model, Graph, Context, Shape = ReadTagSample(Sample)
    FrameValue = ReadDualFrame(Graph, Context)
    assert FrameValue == Sample.Frame
    State = CheckDualLive(
        Graph,
        Context,
        Model,
        Shape,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
        FrameValue,
    )
    assert isinstance(Model.Bodies[0].History, JournalModel)
    assert State == ReadDualLive(
        Model.Bodies[0].History, IntegerValue(Context.Extrude.Fields["endModelHS"])
    )
    assert len(State.Entities) == 48
