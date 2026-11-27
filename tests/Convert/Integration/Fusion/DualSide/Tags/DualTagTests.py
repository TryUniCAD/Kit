from pytest import mark as MarkTests, raises as RaisesError

from convert import open_document as OpenDocument
from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import (
    CheckDualLive,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases
from tests.Convert.Integration.Fusion.DualSide.Tags.ReadTagSample import ReadTagSample


# all native discovery and held out archives retain their explicit admission boundary
@MarkTests.parametrize(
    "Sample", ReadDualCases(), ids=[Value.Identity for Value in ReadDualCases()]
)
def CheckTagArchive(Sample: DualCase) -> None:
    Model, Graph, Context, Shape = ReadTagSample(Sample)
    if Sample.Frame.z_axis.z != 1.0 or Sample.FirstTaper == Sample.SecondTaper == 0:
        with RaisesError(ValueError):
            _ = CheckDualLive(
                Graph,
                Context,
                Model,
                Shape,
                Sample.FirstMm,
                Sample.SecondMm,
                Sample.FirstTaper,
                Sample.SecondTaper,
            )
        if Sample.FirstTaper == Sample.SecondTaper == 0:
            assert len(OpenDocument(Sample.Source).bodies) == 1
        return
    State = CheckDualLive(
        Graph,
        Context,
        Model,
        Shape,
        Sample.FirstMm,
        Sample.SecondMm,
        Sample.FirstTaper,
        Sample.SecondTaper,
    )
    assert isinstance(State, GeometryState)
