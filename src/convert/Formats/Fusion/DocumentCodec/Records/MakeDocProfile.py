from convert.Formats.Fusion.DocumentCodec.Records.MakeSegProfile import MakeSegProfile
from convert.Formats.Fusion.DocumentCodec.Records.MakeTargets import MakeTargets
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# the doc profile operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def MakeDocProfile(
    Schemas: tuple[ClassSchema, ...], Metadata: tuple[MetaSegment, ...], SegmentId: int
) -> EntityProfile:
    Targets = tuple(
        Target
        for Segment in Metadata
        if Segment.Header.SegmentId != SegmentId
        for Target in MakeTargets(Segment)
    )
    Selected = tuple(
        Segment for Segment in Metadata if Segment.Header.SegmentId == SegmentId
    )
    if len(Selected) != 1:
        raise ValueError("Missing or duplicate Fusion document segment identity")
    return MakeSegProfile(Schemas, Selected[0], Targets)
