from struct import pack as PackValue

from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitLocalRef import EmitLocalRef
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def EmitReference(Value: KEntityValue) -> bytes:
    if Value is None or isinstance(Value, LocalRef):
        return EmitLocalRef(Value)
    if not isinstance(Value, SegmentRef) or type(Value.ObjectId) is not int or type(Value.SegmentId) is not int:
        raise ValueError("Invalid Fusion entity reference type")
    if not 0 <= Value.ObjectId < 1 << 64 or not 0 <= Value.SegmentId < 1 << 32:
        raise ValueError("Fusion entity reference identity exceeds wire range")
    return PackValue("<BQBBI", 1, Value.ObjectId, 0, 1, Value.SegmentId)
