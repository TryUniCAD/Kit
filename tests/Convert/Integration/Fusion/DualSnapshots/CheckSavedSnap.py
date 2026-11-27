from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckDualSnaps import (
    CheckDualSnaps,
)
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualSide.ReadDualState import ReadDualState


# complete saved archives must resolve independent live and snapshot tables before correspondence is checked
def CheckSavedSnap(DataValue: bytes) -> None:
    Model = ReadDocument(DataValue)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Shape = ReadCircle(Graph, Context)
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    StateId = Context.Extrude.Fields["endModelHS"]
    assert type(StateId) is int
    LiveState = ReadDualState(History, StateId)
    CheckDualSnaps(Model, Graph, Context, Shape, LiveState)
