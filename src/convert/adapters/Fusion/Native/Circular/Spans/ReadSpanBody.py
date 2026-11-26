from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# one live body must carry one unambiguous native operation identity
def ReadSpanBody(State: GeometryState) -> tuple[BodyNode, FeatureTag]:
    Bodies = tuple(Value for Value in State.Entities if isinstance(Value, BodyNode))
    if len(Bodies) != 1:
        raise ValueError("Native circular span has more than one live body")
    BodyValue = Bodies[0]
    BodyTags = tuple(
        Value
        for Value in State.Entities
        if isinstance(Value, TagAttrib)
        and Value.Links.OwnerRef == State.Entities.index(BodyValue)
    )
    if len(BodyTags) != 1 or len(BodyTags[0].Groups) != 1:
        raise ValueError("Native circular span has no unique body identity")

    return BodyValue, BodyTags[0].Groups[0]
