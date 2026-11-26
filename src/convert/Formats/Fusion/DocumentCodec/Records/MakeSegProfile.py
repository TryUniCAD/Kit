from convert.Formats.Fusion.DocumentCodec.Records.MakeDesignProf import MakeDesignProf
from convert.Formats.Fusion.DocumentCodec.Records.PickVersions import PickVersions
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# each segment needs its own schema policy while foreign targets retain their native identities
def MakeSegProfile(
    Schemas: tuple[ClassSchema, ...],
    Selected: MetaSegment,
    Targets: tuple[ExternalTarget, ...],
) -> EntityProfile:
    if Selected.Header.Segment == SegmentKind.KDesign:
        return MakeDesignProf(Schemas, Selected.Classes, Targets)
    return EntityProfile(
        "98542EB9-A4F2-4137-A808-DBB5B3CD6159",
        PickVersions(Schemas, Selected.Classes),
        Targets,
    )
