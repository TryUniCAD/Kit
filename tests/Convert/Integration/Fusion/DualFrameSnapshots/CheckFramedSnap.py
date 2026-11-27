from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckDualSnaps import (
    CheckDualSnaps,
)
from convert.adapters.Fusion.Native.Circular.DualFrames.ReadDualFrame import (
    ReadDualFrame,
)
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.geometry.Models.Transform import Transform
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState


# complete archives must agree with the recorded qualified frame without changing their world live state
def CheckFramedSnap(DataValue: bytes, Frame: Transform | None = None) -> None:
    Model = ReadDocument(DataValue)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Shape = ReadCircle(Graph, Context)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    CheckRegion(Graph, Context, (Shape.CurveNode,), Model.Asset.AssetId)
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    StateId = Context.Extrude.Fields["endModelHS"]
    assert type(StateId) is int
    LiveState = ReadDualState(History, StateId)
    if Frame is None:
        CheckDualSnaps(Model, Graph, Context, Shape, LiveState)
    else:
        Qualified = ReadDualFrame(Graph, Context)
        assert Qualified == Frame
        CheckDualSnaps(Model, Graph, Context, Shape, LiveState, Qualified)
