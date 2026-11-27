from math import isfinite as IsFinite

from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanLink import CheckSpanLink
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# the original profile source must remain attached to both bottom uses and one finite body clock
def CheckRimLinks(State: GeometryState, Shape: CircleShape, BottomEdge: int) -> None:
    Sketches = tuple(
        Entity for Entity in State.Entities if isinstance(Entity, SketchAttrib)
    )
    SketchUses = {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, CoedgeNode) and Entity.EdgeRef == BottomEdge
    }
    if (
        len(Sketches) != 2
        or len(SketchUses) != 2
        or {Entity.Links.OwnerRef for Entity in Sketches} != SketchUses
    ):
        raise ValueError("Native rim profile source does not own both bottom uses")
    for Entity in Sketches:
        CheckSpanLink(State, Entity, Shape)
    Clocks = tuple(
        Entity for Entity in State.Entities if isinstance(Entity, TimeAttrib)
    )
    if (
        len(Clocks) != 1
        or not isinstance(State.Entities[Clocks[0].Links.OwnerRef], BodyNode)
        or not IsFinite(Clocks[0].UnixMicros)
        or Clocks[0].UnixMicros < 0
    ):
        raise ValueError("Native rim has an unsupported body timestamp")
