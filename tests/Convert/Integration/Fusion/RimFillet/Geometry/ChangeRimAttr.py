from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib


# attribution corruption must preserve native field kinds while violating physical ownership
def ChangeRimAttr(
    Entity: KJournalEntity, CaseName: str, ReferenceId: int
) -> KJournalEntity:
    if isinstance(Entity, TimeAttrib) and CaseName == "body_clock":
        return ReplaceData(Entity, UnixMicros=-1.0)
    if isinstance(Entity, SketchAttrib) and CaseName == "bottom_source":
        return ReplaceData(
            Entity,
            SourceLink=ReplaceData(
                Entity.SourceLink, PrimaryId=Entity.SourceLink.PrimaryId + 1
            ),
        )
    if isinstance(Entity, TagAttrib) and CaseName == "attribute_cycle":
        return ReplaceData(
            Entity, Links=ReplaceData(Entity.Links, NextAttrib=ReferenceId)
        )
    if isinstance(Entity, TagAttrib) and CaseName == "blend_operation":
        Group = Entity.Groups[0]
        return ReplaceData(
            Entity,
            Groups=(
                ReplaceData(
                    Group, OperationIds=tuple(Value + 1 for Value in Group.OperationIds)
                ),
            ),
        )
    raise ValueError("Unknown rim attribute corruption")
