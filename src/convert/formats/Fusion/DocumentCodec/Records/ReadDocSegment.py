from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


def ReadDocSegment(
    Streams: SegmentStreams, Metadata: MetaSegment, Profile: EntityProfile
) -> ParsedSegment:
    if Streams.SegmentId != Metadata.Header.SegmentId:
        raise ValueError("Fusion segment identity disagrees with its metadata")
    Records = tuple(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            Streams.BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in ReadBulkSpans(
            Streams.BulkData, Streams.Metadata, Segment=Metadata.Header.Segment
        )
    )
    return ParsedSegment(
        Metadata, DecodeEntities(Records, Metadata.Classes, Profile), Profile
    )
