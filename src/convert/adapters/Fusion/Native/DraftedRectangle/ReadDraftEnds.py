from convert.adapters.Fusion.Native.DraftedRectangle.MatchDraftVerts import (
    MatchDraftVerts,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


# sketch links must remain on one drafted cap or its independently validated auxiliary profile
def ReadDraftEnds(
    Table: LiveTable,
    SavedEdge: EdgeNode,
    Vertices: dict[int, int],
    Points: tuple[tuple[float, float, float], ...],
) -> frozenset[tuple[float, float]]:
    Start = StableRef(Table, SavedEdge.StartVertex)
    Finish = StableRef(Table, SavedEdge.EndVertex)
    if Start in Vertices and Finish in Vertices:
        First, Final = Vertices[Start], Vertices[Finish]
        if First // 4 != Final // 4:
            raise ValueError("Native drafted sketch link belongs to a wall rail")
        return frozenset((Points[First % 4][:2], Points[Final % 4][:2]))
    if Start in Vertices or Finish in Vertices:
        raise ValueError(
            "Native drafted sketch link mixes solid and auxiliary ownership"
        )
    FirstPoint = ReadVertexPoint(Table, Start)
    LastPoint = ReadVertexPoint(Table, Finish)
    if FirstPoint[2] != 0 or LastPoint[2] != 0:
        raise ValueError(
            "Native drafted auxiliary sketch link leaves its profile plane"
        )
    return frozenset(
        Points[Index][:2]
        for Index in MatchDraftVerts((FirstPoint, LastPoint), Points[:4])
    )
