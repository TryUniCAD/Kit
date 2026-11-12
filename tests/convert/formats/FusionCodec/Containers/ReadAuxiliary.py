from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


def ReadAuxiliary(
    Streams: SegmentStreams, Profile: EntityProfile, Segment: SegmentKind
) -> tuple[EntityRecord, ...]:
    Metadata = ReadMetaWire(Streams.Metadata, Segment=Segment)
    Spans = ReadBulkSpans(Streams.BulkData, Streams.Metadata, Segment=Segment)
    Records = tuple(
        BulkRecord(
            Span.TypeCode,
            Span.ObjectId,
            Span.IsPrimary,
            Streams.BulkData[Span.PayloadOffset : Span.EndOffset],
        )
        for Span in Spans
    )
    return DecodeEntities(Records, Metadata.Classes, Profile)
