from collections import Counter as CountLabels
from convert.adapters.Fusion.Native.DraftedRectangle.MatchDraftPoints import (
    MatchDraftPoints,
)

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# drafted cap links retain their selected source curve even when the upper cap expands or contracts
def CheckDraftEdges(
    Table: LiveTable,
    Vertices: dict[int, int],
    Points: tuple[tuple[float, float, float], ...],
    Curves: dict[int, frozenset[tuple[float, float]]],
    Count: int,
    Excluded: frozenset[int] = frozenset(),
) -> None:
    Labels: CountLabels[int] = CountLabels()
    for Slot in Table.LiveSlots:
        Value = Table.Entities[Slot]
        if not isinstance(Value, SketchAttrib) or Slot in Excluded:
            continue
        Owner = StableRef(Table, Value.Links.OwnerRef)
        Coedge = Table.Entities[Owner]
        Direction = int(not isinstance(Coedge, CoedgeNode))
        Edge = RequireLive(
            Table,
            (
                StableRef(Table, Coedge.EdgeRef)
                if isinstance(Coedge, CoedgeNode)
                else Owner
            ),
            EdgeNode,
        )
        Start = StableRef(Table, Edge.StartVertex)
        Finish = StableRef(Table, Edge.EndVertex)
        if Start in Vertices and Finish in Vertices:
            First, Last = Vertices[Start], Vertices[Finish]
            if First // 4 != Last // 4:
                raise ValueError("Native drafted sketch link belongs to a wall rail")
            Endpoints = frozenset((Points[First % 4][:2], Points[Last % 4][:2]))
        elif Start not in Vertices and Finish not in Vertices:
            FirstPoint = ReadVertexPoint(Table, Start)
            LastPoint = ReadVertexPoint(Table, Finish)
            if FirstPoint[2] != 0 or LastPoint[2] != 0:
                raise ValueError(
                    "Native drafted auxiliary sketch link leaves its profile plane"
                )
            Endpoints = frozenset(
                Points[Index][:2]
                for Index in MatchDraftPoints((FirstPoint, LastPoint), Points[:4])
            )
        else:
            raise ValueError(
                "Native drafted sketch link mixes solid and auxiliary ownership"
            )
        Link = Value.SourceLink
        if (
            Link.PrimaryId not in Curves
            or Link != SketchLink(Link.PrimaryId, 0, Direction, 1, 1)
            or Endpoints != Curves[Link.PrimaryId]
        ):
            raise ValueError(
                "Native drafted sketch link belongs to a different selected curve"
            )
        Labels[Link.PrimaryId] += 1
    if dict(Labels) != dict.fromkeys(Curves, Count):
        raise ValueError("Native drafted sketch source link coverage is incomplete")
