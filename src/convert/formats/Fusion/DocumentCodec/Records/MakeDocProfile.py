from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


def MakeDocProfile(
    Schemas: tuple[ClassSchema, ...], Metadata: tuple[MetaSegment, ...], SegmentId: int
) -> EntityProfile:
    Targets = tuple(
        ExternalTarget(Segment.Header.SegmentId, ObjectId, ClassValue.ClassGuid)
        for Segment in Metadata
        if Segment.Header.SegmentId != SegmentId
        for ClassValue in Segment.Classes
        for ObjectId in ClassValue.OwnerIds
    )
    return EntityProfile("98542EB9-A4F2-4137-A808-DBB5B3CD6159", Schemas, Targets)
