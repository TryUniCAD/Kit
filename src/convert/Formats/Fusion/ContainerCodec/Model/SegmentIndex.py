from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# downstream record decoding can reuse the metadata and spans verified during container validation
@MakeDataClass(frozen=True, slots=True)
class SegmentIndex:
    Metadata: MetaSegment
    Spans: tuple[RecordSpan, ...]
