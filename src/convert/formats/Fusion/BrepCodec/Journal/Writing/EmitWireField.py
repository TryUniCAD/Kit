from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.formats.Fusion.GeometryCodec.EncodeSmbString import EncodeSmbString
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def EmitWireField(Field: KAsmToken) -> bytes:
    TagValue, Value = Field
    if TagValue in (4, 12, 21):
        if type(Value) is not int or not -(1 << 31) <= Value < (1 << 31):
            raise ValueError("Fusion journal integer exceeds native signed 32 bits")
        return bytes((TagValue,)) + PackValue("<q", Value)
    if TagValue in (13, 14) and type(Value) is str and Value and Value.isascii():
        return EncodeSmbString(TagValue, Value)
    if TagValue in (15, 16) and Value is None:
        return bytes((TagValue,))
    if (
        TagValue == 6
        and isinstance(Value, (int, float))
        and not isinstance(Value, bool)
        and IsFinite(Value)
    ):
        return b"\x06" + PackValue("<d", Value)
    if TagValue == 7 and type(Value) is str and Value.isascii() and "\0" not in Value:
        return EncodeSmbString(7, Value)
    if TagValue in (10, 11) and Value is None:
        return bytes((TagValue,))
    if TagValue in (19, 20) and isinstance(Value, tuple) and len(Value) == 3:
        if all(type(Number) in (int, float) and IsFinite(Number) for Number in Value):
            return bytes((TagValue,)) + PackValue("<3d", *Value)
    raise ValueError("Invalid Fusion journal wire field")
