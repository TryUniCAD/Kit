from convert.adapters.Fusion.Native.DraftedRectangle.CheckDraftSolid import (
    CheckDraftSolid,
)
from convert.adapters.Fusion.Native.DraftedRectangle.CheckDraftTags import (
    CheckDraftTags,
)
from convert.adapters.Fusion.Native.DraftedRectangle.CheckDraftCache import (
    CheckDraftCache,
)
from convert.adapters.Fusion.Native.DraftedRectangle.ReadDraftSheets import (
    ReadDraftSheets,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import (
    ReadInsert,
)
from convert.adapters.Fusion.Native.SignedPrism.SignedBody import SignedBody
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.Geometry.Extrude.Polygon.DraftMass import DraftMass
from interchange.brep.Topology.BrepModel import BrepModel


# typed insertion history and its independent snapshot must prove the same complete drafted rectangle
def ReadDraftBody(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    Geometry: BrepModel,
    Measures: DraftMass,
) -> None:
    if len(Model.Bodies) != 1 or len(Model.Snapshots) != 1:
        raise ValueError(
            "Native drafted rectangle requires one body history and one snapshot"
        )
    History = Model.Bodies[0].History
    if isinstance(History, PrismHistory):
        History = ReadJournal(EmitBodyPart(Model.Bodies[0]).Payload)
    Snapshot = Model.Snapshots[0].Snapshot
    if not isinstance(History, JournalModel) or not isinstance(Snapshot, GeometryState):
        raise ValueError(
            "Native drafted rectangle requires typed planar history and snapshot"
        )
    JournalTable, Journal = ReadInsert(History)
    CheckDraftCache(Graph, Context, Model, Snapshot)
    Slots = tuple(range(len(Snapshot.Entities)))
    SavedTable = LiveTable(Journal.StateId, Snapshot.Entities, Slots, Slots, Slots)
    Saved = ReadPlacedBody(SavedTable, 1)
    JournalIds = CheckDraftSolid(Journal, Geometry, Measures)
    SavedIds = CheckDraftSolid(Saved, Geometry, Measures)
    Edges = {
        EdgeUse.EdgeRef
        for Surface in ReadBodyFaces(SavedTable, Saved.BodyRef)
        for EdgeUse in Surface.BoundaryUses
    }
    if len(Edges) != 12:
        raise ValueError(
            "Native drafted rectangle snapshot must have twelve distinct edges"
        )
    Regions, Retired = ReadDraftSheets(Snapshot, SavedTable, Saved, Shape)
    CheckDraftTags(
        Graph,
        Context,
        Model,
        Shape,
        History,
        SignedBody(Journal, Saved, JournalTable, SavedTable, Regions),
        Geometry,
        JournalIds,
        SavedIds,
        Retired,
    )
