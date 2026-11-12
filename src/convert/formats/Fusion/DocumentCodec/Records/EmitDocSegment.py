from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment


def EmitDocSegment(Value: ParsedSegment) -> SegmentStreams:
    Records = EncodeEntities(Value.Records, Value.Metadata.Classes, Value.Profile)
    BulkData, MetaData = EmitSegment(Value.Metadata, Records)
    return SegmentStreams(Value.Metadata.Header.SegmentId, MetaData, BulkData)
