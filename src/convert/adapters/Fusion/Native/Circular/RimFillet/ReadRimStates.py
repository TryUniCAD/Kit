from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLive import ReadDualLive
from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# both retained solids must belong to the actual current single body feature history
def ReadRimStates(
    Model: DocumentModel, Context: RimContext
) -> tuple[GeometryState, GeometryState]:
    if len(Model.Bodies) != 1 or Model.Forms or Model.Meshes:
        raise ValueError("Native rim requires one complete solid history")
    History = Model.Bodies[0].History
    if not isinstance(History, JournalModel):
        raise ValueError("Native rim requires typed journal history")
    StartId = IntegerValue(Context.Feature.Fields["startModelHS"])
    FinishId = IntegerValue(Context.Feature.Fields["endModelHS"])
    if History.Header.IntWidth not in (4, 8) or History.Header != BrepHeader(
        23200, 2, 3, 50.0, 1e-6, 1e-10, History.Header.IntWidth
    ):
        raise ValueError("Native rim history has unqualified framing")
    if (
        StartId != Context.Extrusion.Extrude.Fields["endModelHS"]
        or FinishId != History.Stream.CurrentStateId
        or FinishId != History.Stream.MaxStateId
        or History.States[History.Stream.InitialNode].StateId
        != Context.Extrusion.Extrude.Fields["startModelHS"]
    ):
        raise ValueError("Native rim history is rolled back or has another predecessor")
    Prior = ReadDualLive(History, StartId)
    Current = ReadDualLive(History, FinishId)
    BodyValue, _ = ReadSpanBody(Current)
    if History.Stream.NextEntityTag <= BodyValue.Prefix.EntityTag:
        raise ValueError("Native rim history reuses an allocated body identity")
    return Prior, Current
