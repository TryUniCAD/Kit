from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import FieldValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def EmitLocalRef(Value: FieldValue) -> bytes:
    if Value is None:
        return b"\0"
    if (
        not isinstance(Value, LocalRef)
        or type(Value.ObjectId) is not int
        or not 0 <= Value.ObjectId < 1 << 64
    ):
        raise ValueError("Invalid Fusion feature local reference")
    return PackValue("<BQH", 1, Value.ObjectId, 0)
