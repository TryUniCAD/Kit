from collections import Counter as CountLabels
from convert.adapters.Fusion.Native.DraftedRectangle.ReadDraftEnds import (
    ReadDraftEnds,
)

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# drafted cap links retain their selected source curve even when the upper cap expands or contracts
def CheckDraftEdges(
    Table: LiveTable,
    Vertices: dict[int, int],
    Points: tuple[tuple[float, float, float], ...],
    Curves: dict[int, frozenset[tuple[float, float]]],
    Count: int,
    Excluded: frozenset[int],
) -> None:
    Labels: CountLabels[int] = CountLabels()
    for SlotIndex in Table.LiveSlots:
        Value = Table.Entities[SlotIndex]
        if not isinstance(Value, SketchAttrib) or SlotIndex in Excluded:
            continue
        Owner = StableRef(Table, Value.Links.OwnerRef)
        Coedge = Table.Entities[Owner]
        Direction = int(not isinstance(Coedge, CoedgeNode))
        SavedEdge = RequireLive(
            Table,
            (
                StableRef(Table, Coedge.EdgeRef)
                if isinstance(Coedge, CoedgeNode)
                else Owner
            ),
            EdgeNode,
        )
        Endpoints = ReadDraftEnds(Table, SavedEdge, Vertices, Points)
        SourceLink = Value.SourceLink
        if (
            SourceLink.PrimaryId not in Curves
            or SourceLink != SketchLink(SourceLink.PrimaryId, 0, Direction, 1, 1)
            or Endpoints != Curves[SourceLink.PrimaryId]
        ):
            raise ValueError(
                "Native drafted sketch link belongs to a different selected curve"
            )
        Labels[SourceLink.PrimaryId] += 1
    if dict(Labels) != dict.fromkeys(Curves, Count):
        raise ValueError("Native drafted sketch source link coverage is incomplete")
