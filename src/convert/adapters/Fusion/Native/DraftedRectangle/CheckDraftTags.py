from dataclasses import replace as ReplaceValue
from convert.adapters.Fusion.Native.DraftedRectangle.MatchDraftVerts import (
    MatchDraftVerts,
)

from convert.adapters.Fusion.Native.DraftedRectangle.CheckDraftEdges import (
    CheckDraftEdges,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedOwners import CheckOwnTags
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import (
    CheckFaceTags,
    CheckRegionTags,
    ReadFeatureTags,
    SelectedCurves,
)
from convert.adapters.Fusion.Native.SignedPrism.SignedBody import SignedBody
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.brep.Topology.BrepModel import BrepModel


# both independent geometry roles must attach every drafted face and edge to the selected operation and sketch
def CheckDraftTags(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    History: JournalModel,
    Bodies: SignedBody,
    Geometry: BrepModel,
    JournalIds: tuple[int, ...],
    SavedIds: tuple[int, ...],
    Retired: frozenset[int],
) -> None:
    FaceTags = ReadFeatureTags(Bodies.JournalTable)
    BodyTag = FaceTags.pop(Bodies.Journal.BodyRef, None)
    if BodyTag is None:
        raise ValueError("Native drafted rectangle has no owned body tag")
    Operation, Sides = CheckOwnTags(
        Graph, Context, Model, Shape, History, Bodies.Journal, BodyTag
    )
    Curves = SelectedCurves(Shape)
    if set(Sides.values()) != set(Curves):
        raise ValueError("Native drafted side tags omit selected sketch curves")
    Points = tuple(
        (Vertex.point.x / 10, Vertex.point.y / 10, Vertex.point.z / 10)
        for Vertex in Geometry.vertices
    )
    Journal = ReplaceValue(
        Bodies.Journal, PointsCm=tuple(Points[Index] for Index in JournalIds)
    )
    Saved = ReplaceValue(
        Bodies.Saved, PointsCm=tuple(Points[Index] for Index in SavedIds)
    )
    if CheckFaceTags(
        Journal, FaceTags, Operation, Points[4][2], Sides, Curves
    ) != CheckFaceTags(
        Saved,
        ReadFeatureTags(Bodies.SavedTable),
        Operation,
        Points[4][2],
        Sides,
        Curves,
    ):
        raise ValueError("Native drafted history and snapshot face identities disagree")
    for Region in Bodies.Regions:
        CheckRegionTags(
            ReplaceValue(
                Region,
                CornersCm=tuple(
                    Points[Index]
                    for Index in MatchDraftVerts(Region.CornersCm, Points[:4])
                ),
            ),
            Curves,
        )
    CheckDraftEdges(
        Bodies.JournalTable,
        dict(zip(Journal.VertexRefs, JournalIds, strict=True)),
        Points,
        Curves,
        2,
        frozenset(),
    )
    CheckDraftEdges(
        Bodies.SavedTable,
        dict(zip(Saved.VertexRefs, SavedIds, strict=True)),
        Points,
        Curves,
        6,
        Retired,
    )
