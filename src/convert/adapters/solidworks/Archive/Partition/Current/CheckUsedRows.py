from collections.abc import Mapping

from convert.Geometry.Parasolid import CollectPartTopo, RecordTables
from convert.adapters.solidworks.Archive.Partition.Current.CheckCarrier import (
    CheckCarrier,
)
from convert.adapters.solidworks.Archive.Partition.Current.CheckFinLinks import (
    CheckFinLinks,
)
from convert.adapters.solidworks.Archive.Partition.Current.CheckTopoRows import (
    CheckTopoRows,
)
from convert.adapters.solidworks.Archive.Partition.Current.CheckUsedRanks import (
    CheckUsedRanks,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# vertex recovery cannot admit unrelated scanner topology or carrier families
def CheckUsedRows(
    BodyData: bytes,
    Tables: RecordTables,
    Nodes: Mapping[int, XmtNode],
    Spans: Mapping[int, tuple[int, int]],
) -> None:
    if Tables.entities:
        raise ValueError("recovered topology has an unqualified scanner body hierarchy")
    (
        FaceLoops,
        _,
        EdgeCurves,
        _,
        FinIds,
        Edges,
        Vertices,
        Curves,
        Surfaces,
        NewVertices,
        NewCurves,
        _,
    ) = CollectPartTopo(Tables)
    if NewVertices or NewCurves:
        raise ValueError("recovered topology uses unqualified synthetic geometry")
    Loops = {LoopIndex for Items in FaceLoops.values() for LoopIndex, _ in Items}
    Points = {Tables.vertex_uses[Vertex].references[4] for Vertex in Vertices}
    for Selected, Records, KindValue in (
        (FaceLoops, Tables.bridges, 14),
        (Loops, Tables.loops, 15),
        (Edges, Tables.edge_uses, 16),
        (FinIds, Tables.coedges, 17),
        (Points, Tables.points, 29),
    ):
        CheckTopoRows(Selected, Records, KindValue, Nodes, Spans)
    CheckFinLinks(FinIds, Edges, Vertices, Tables)
    FaceSurfaces = {
        FaceId: Tables.bridges[FaceId].references[4] for FaceId in FaceLoops
    }
    for Selected, Carriers, KindValue, Owners in (
        (Curves, Tables.curves, 30, EdgeCurves),
        (Surfaces, Tables.surfaces, 50, FaceSurfaces),
    ):
        for IndexValue in Selected:
            CheckCarrier(
                BodyData,
                IndexValue,
                Carriers[IndexValue],
                KindValue,
                Owners,
                Nodes,
                Spans,
            )
    CheckUsedRanks(Tables, Edges, Points, Curves, Surfaces)
