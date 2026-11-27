from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.ContainerCodec.Model.SegmentIndex import SegmentIndex
from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.Records.DecodeSegment import DecodeSegment
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# the doc segment operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadDocSegment(
    Streams: SegmentStreams, Metadata: MetaSegment, Profile: EntityProfile
) -> ParsedSegment:
    if Streams.SegmentId != Metadata.Header.SegmentId:
        raise ValueError("Fusion segment identity disagrees with its metadata")
    Spans = ReadBulkSpans(
        Streams.BulkData, Streams.Metadata, Segment=Metadata.Header.Segment
    )
    return DecodeSegment(Streams.BulkData, SegmentIndex(Metadata, Spans), Profile)
