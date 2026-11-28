from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# foreign references need segment scoped owners in the order stored in metadata
def MakeTargets(Segment: MetaSegment) -> tuple[ExternalTarget, ...]:
    SegmentId = Segment.Header.SegmentId
    return tuple(
        ExternalTarget(SegmentId, ObjectId, ClassValue.ClassGuid)
        for ClassValue in Segment.Classes
        for ObjectId in ClassValue.OwnerIds
    )
