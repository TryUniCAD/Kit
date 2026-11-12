from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import PackHistRef
from convert.formats.Fusion.SegmentCodec.Parameters.NumberBinding import NumberBinding
from convert.formats.Fusion.SegmentCodec.Parameters.ParamSink import ParamSink


def EmitNumBinding(Value: NumberBinding) -> bytes:
    if not isinstance(Value, NumberBinding):
        raise ValueError("Expected a typed Fusion numeric binding")
    References = tuple(
        PackHistRef(Identity)
        for Identity in (Value.OwnerId, Value.ParamId, Value.BookId)
    )
    if (
        0 in (Value.OwnerId, Value.ParamId, Value.BookId)
        or len(set(References)) != 3
        or type(Value.BoundRank) is not int
        or not 1 <= Value.BoundRank < 1 << 32
    ):
        raise ValueError("Invalid Fusion numeric binding identities or rank")
    Owner, Param, BookRef = References
    Output = ParamSink()
    Output.AddBytes(bytes(4) + b"\1\1\0\0\0" + Owner)
    Output.AddWord(Value.SlotIndex)
    Output.AddBytes(bytes(1))
    Output.AddNumber(Value.Number)
    Output.AddBytes(Param)
    Output.AddWord(Value.BoundRank)
    Output.AddBytes(bytes(4) + Owner + b"\1\0\0" + BookRef + bytes(1) + Owner)
    return bytes(Output.Buffer)
