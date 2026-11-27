from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


# every retained attribute needs one complete reciprocal chain rather than an unowned side table
def CheckRimAttrs(State: GeometryState) -> None:
    Attributes = {
        Index: Entity
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, (TagAttrib, SketchAttrib, TrackAttrib, TimeAttrib))
    }
    SeenSlots: set[int] = set()
    for Index, Entity in enumerate(State.Entities):
        if Index in Attributes:
            if isinstance(Entity, TagAttrib) and Entity.Attribute != -1:
                raise ValueError("Native rim labels contain unqualified nested records")
            continue
        HeadRef = MakeEntityNode(Entity).Tokens[0][1]
        if type(HeadRef) is not int:
            raise ValueError("Native rim attribute head is not a reference")
        Prior = -1
        while HeadRef != -1:
            if HeadRef not in Attributes or HeadRef in SeenSlots:
                raise ValueError("Native rim attribute chain is cyclic or missing")
            Attribute = Attributes[HeadRef]
            if (
                Attribute.Links.OwnerRef != Index
                or Attribute.Links.PriorAttrib != Prior
            ):
                raise ValueError("Native rim attribute ownership is not reciprocal")
            SeenSlots.add(HeadRef)
            Prior, HeadRef = HeadRef, Attribute.Links.NextAttrib
    if SeenSlots != set(Attributes):
        raise ValueError("Native rim has unaccounted live attributes")
