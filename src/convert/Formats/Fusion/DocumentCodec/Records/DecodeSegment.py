from convert.Formats.Fusion.ContainerCodec.Model.SegmentIndex import SegmentIndex
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.Records.SlackLimit import (
    KMaxDesignSlack,
    KSlackKinds,
)
from convert.Formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.Formats.Fusion.EntityCodec.DecodeSlack import DecodeSlack
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.MetaIndex import SegmentKind
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


# record decoding needs the verified ownership and payload boundaries from the segment index
def DecodeSegment(
    BulkData: bytes, IndexValue: SegmentIndex, Profile: EntityProfile
) -> ParsedSegment:
    Metadata = IndexValue.Metadata
    Records = tuple(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in IndexValue.Spans
    )
    KindValue = Metadata.Header.Segment
    if KindValue not in KSlackKinds:
        Values = DecodeEntities(Records, Metadata.Classes, Profile)
        return ParsedSegment(Metadata, Values, Profile)
    Values, Slack = DecodeSlack(Records, Metadata.Classes, Profile)
    if KindValue is SegmentKind.KDesign and len(Slack) > KMaxDesignSlack:
        raise ValueError("Unexplained trailing Fusion entity payload bytes")
    return ParsedSegment(Metadata, Values, Profile, Slack)
