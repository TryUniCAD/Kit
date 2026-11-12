from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment


def EmitDocSegment(Value: ParsedSegment) -> SegmentStreams:
    if type(Value.BulkSlack) is not bytes:
        raise ValueError("Fusion bulk slack must be bytes")
    if Value.BulkSlack and Value.Metadata.Header.Segment is not SegmentKind.KAct:
        raise ValueError("Only the Fusion ACT bulk stream carries slack")
    Records = EncodeEntities(Value.Records, Value.Metadata.Classes, Value.Profile)
    BulkData, MetaData = EmitSegment(Value.Metadata, Records)
    return SegmentStreams(
        Value.Metadata.Header.SegmentId, MetaData, BulkData + Value.BulkSlack
    )
