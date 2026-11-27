from math import isfinite as IsFinite

from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLabel import (
    ReadDualLabel,
)
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanLink import CheckSpanLink
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


# every retained attribute requires a reciprocal owner chain and exact profile source scope
def CheckDualLinks(
    State: GeometryState,
    Shape: CircleShape,
    FirstMm: float,
    SecondMm: float,
) -> None:
    Attributes = {
        Index: Entity
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, (TagAttrib, SketchAttrib, TimeAttrib))
    }
    SeenSlots: set[int] = set()
    for Index, Entity in enumerate(State.Entities):
        if Index in Attributes:
            continue
        HeadRef = MakeEntityNode(Entity).Tokens[0][1]
        if type(HeadRef) is not int:
            raise ValueError("Native dual side attribute head is not a reference")
        Prior = -1
        while HeadRef != -1:
            if HeadRef not in Attributes or HeadRef in SeenSlots:
                raise ValueError("Native dual side attribute chain is cyclic or absent")
            Attribute = Attributes[HeadRef]
            if (
                Attribute.Links.OwnerRef != Index
                or Attribute.Links.PriorAttrib != Prior
            ):
                raise ValueError(
                    "Native dual side attribute ownership is not reciprocal"
                )
            SeenSlots.add(HeadRef)
            Prior, HeadRef = HeadRef, Attribute.Links.NextAttrib
    if SeenSlots != set(Attributes):
        raise ValueError("Native dual side attributes are not fully owned")
    Sketches = tuple(
        Entity for Entity in Attributes.values() if isinstance(Entity, SketchAttrib)
    )
    JointUses = {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, CoedgeNode)
        and ReadDualLabel(State, Entity.EdgeRef, FirstMm, SecondMm) == "joint"
    }
    if (
        len(Sketches) != 2
        or {Entity.Links.OwnerRef for Entity in Sketches} != JointUses
    ):
        raise ValueError("Native dual side sketch links do not own the profile joint")
    for Entity in Sketches:
        CheckSpanLink(State, Entity, Shape)
    Times = tuple(
        Entity for Entity in Attributes.values() if isinstance(Entity, TimeAttrib)
    )
    if (
        len(Times) != 1
        or not isinstance(State.Entities[Times[0].Links.OwnerRef], BodyNode)
        or not IsFinite(Times[0].UnixMicros)
        or Times[0].UnixMicros < 0
    ):
        raise ValueError(
            "Native dual side time attribute has an unsupported owner or value"
        )
