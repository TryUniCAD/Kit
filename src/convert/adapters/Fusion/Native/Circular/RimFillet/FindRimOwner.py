from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# full feature tags must resolve to one physical item of the required topology kind
def FindRimOwner(
    State: GeometryState, Group: FeatureTag, ClassType: type[FaceNode] | type[EdgeNode]
) -> int:
    Owners = tuple(
        Entity.Links.OwnerRef
        for Entity in State.Entities
        if isinstance(Entity, TagAttrib) and Entity.Groups == (Group,)
    )
    if len(Owners) != 1 or not isinstance(State.Entities[Owners[0]], ClassType):
        raise ValueError("Native rim recipe does not select one physical owner")
    return Owners[0]
