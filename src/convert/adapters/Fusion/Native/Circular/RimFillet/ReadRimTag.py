from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# a physical topology item requires exactly one complete native feature group
def ReadRimTag(State: GeometryState, OwnerIndex: int) -> FeatureTag:
    Attributes = tuple(
        Entity
        for Entity in State.Entities
        if isinstance(Entity, TagAttrib) and Entity.Links.OwnerRef == OwnerIndex
    )
    if (
        len(Attributes) != 1
        or len(Attributes[0].Groups) != 1
        or Attributes[0].Attribute != -1
    ):
        raise ValueError("Native rim physical item has ambiguous or extended labels")
    return Attributes[0].Groups[0]
