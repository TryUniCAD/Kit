from dataclasses import replace as CopyData

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity


# one semantic corruption must survive encoding without changing unrelated record ownership
def MutateSnapNode(Entity: KJournalEntity, ModeName: str) -> KJournalEntity | None:
    if ModeName == "identity" and isinstance(Entity, FaceNode):
        return CopyData(Entity, Prefix=CopyData(Entity.Prefix, EntityTag=991))
    if ModeName == "feature" and isinstance(Entity, TagAttrib):
        return CopyData(
            Entity,
            Groups=(CopyData(Entity.Groups[0], PrimaryId="991"), *Entity.Groups[1:]),
        )
    if ModeName == "sketch" and isinstance(Entity, SketchAttrib):
        return CopyData(
            Entity,
            SourceLink=CopyData(
                Entity.SourceLink, PrimaryId=Entity.SourceLink.PrimaryId + 1
            ),
        )
    if ModeName == "geometry" and isinstance(Entity, PointNode):
        return CopyData(
            Entity,
            PositionCm=(
                Entity.PositionCm[0] + 0.01,
                Entity.PositionCm[1],
                Entity.PositionCm[2],
            ),
        )
    return None
