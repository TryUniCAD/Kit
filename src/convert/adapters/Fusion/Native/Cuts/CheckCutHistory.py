from convert.adapters.Fusion.Native.Cuts.ReadCutState import ReadCutState
from convert.adapters.Fusion.Native.Cuts.CheckCutLive import CheckCutLive
from convert.adapters.Fusion.Native.Cuts.CheckCutSolid import CheckCutSolid
from convert.adapters.Fusion.Native.Cuts.CheckCutLabels import CheckCutLabels
from convert.adapters.Fusion.Native.Cuts.CheckCutCache import CheckCutCache
from convert.adapters.Fusion.Native.Cuts.MakeCutLabels import MakeCutLabels
from convert.adapters.Fusion.Native.Cuts.ReadCutOps import ReadCutOps
from convert.adapters.Fusion.Native.Cuts.PrismRings import PrismRings
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanStore import CheckSpanStore
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from interchange.geometry.Models.VectorPlane import PlaneVector


# stock and final states must match their generated boundaries with complete native ownership and caches
def CheckCutHistory(
    Graph: NativeGraph,
    Contexts: tuple[ExtrudeContext, ExtrudeContext],
    Model: DocumentModel,
    Shapes: tuple[RectGeometry, RectGeometry],
    Outline: tuple[PlaneVector, ...],
    Heights: tuple[float, float],
    BodyTag: FeatureTag,
) -> None:
    if len(Model.Bodies) != 1 or len(Model.Snapshots) != 1:
        raise ValueError(
            "Native corner cut requires one typed journal and cache snapshot"
        )
    History, Snapshot = Model.Bodies[0].History, Model.Snapshots[0].Snapshot
    if not isinstance(History, JournalModel) or not isinstance(Snapshot, GeometryState):
        raise ValueError("Native corner cut requires complete typed geometry")
    Stock, ToolCut = Contexts
    Stream = History.Stream
    if (
        Stream.CurrentStateId != Stream.MaxStateId
        or Stream.CurrentStateId != ToolCut.Extrude.Fields["endModelHS"]
        or History.States[Stream.InitialNode].StateId
        != Stock.Extrude.Fields["startModelHS"]
        or Stock.Extrude.Fields["endModelHS"] != ToolCut.Extrude.Fields["startModelHS"]
    ):
        raise ValueError(
            "Native corner cut history boundaries are rolled back or disconnected"
        )
    Operations = ReadCutOps(Graph, Contexts)
    Profiles = (tuple(LineValue.start for LineValue in Shapes[0].Lines), Outline)
    Tables = tuple(
        ReadCutState(History, IntegerValue(Context.Extrude.Fields["endModelHS"]))
        for Context in Contexts
    )
    for Profile, (Table, BodyRef) in zip(Profiles, Tables, strict=True):
        CheckCutLive(Table)
        Rings = PrismRings(Profile, 0.0, Heights[0])
        CheckCutSolid(Table, BodyRef, Rings)
        CheckCutLabels(
            Table,
            BodyRef,
            Rings,
            MakeCutLabels(Graph, Contexts, Shapes, Profile, Operations),
            BodyTag,
        )
    FinalTable, FinalRef = Tables[-1]
    BodyValue = FinalTable.Entities[FinalRef]
    if (
        not isinstance(BodyValue, BodyNode)
        or Stream.NextEntityTag <= BodyValue.Prefix.EntityTag
    ):
        raise ValueError("Native corner cut body identity exceeds its allocator")
    CheckSpanStore(Graph, Stock, Model, BodyValue)
    CheckCutCache(Snapshot, Shapes, Heights)
