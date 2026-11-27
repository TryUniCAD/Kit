from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


# independent malformed groups and source links challenge the full persisted attribution boundary
def ChangeTagNode(
    Entity: KJournalEntity, CaseName: str, Reference: int
) -> KJournalEntity:
    if isinstance(Entity, SketchAttrib):
        if CaseName == "sketch_owner":
            return ReplaceData(Entity, Links=ReplaceData(Entity.Links, OwnerRef=1))
        return ReplaceData(
            Entity, SourceLink=ReplaceData(Entity.SourceLink, PrimaryId=999)
        )
    if isinstance(Entity, TimeAttrib):
        return ReplaceData(Entity, UnixMicros=-1.0)
    assert isinstance(Entity, TagAttrib)
    if CaseName == "attribute_chain":
        return ReplaceData(
            Entity, Links=ReplaceData(Entity.Links, NextAttrib=Reference)
        )
    if CaseName == "joint_missing":
        return ReplaceData(Entity, Groups=Entity.Groups[:1])
    if CaseName == "joint_reversed":
        return ReplaceData(Entity, Groups=Entity.Groups[::-1])
    Group = Entity.Groups[0]
    if CaseName == "body_secondary":
        Group = ReplaceData(Group, SecondaryId=Group.SecondaryId + 1)
    elif CaseName == "side_operation":
        Group = ReplaceData(Group, OperationIds=(999,))
    else:
        Group = ReplaceData(Group, PrimaryId="999")
    return ReplaceData(Entity, Groups=(Group, *Entity.Groups[1:]))
