from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# packed ghost counts derive from the modeled list while retaining its independent flag nibble
def WriteGhostMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    CountValue = len(ReadBodyRows(FrameValue.ScopeValue, RuleValue.CountValue))
    if CountValue >= 0x10000000:
        raise ValueError("native packed ghost count exceeds its low bits")
    FlagsValue = CastValue(
        int, ReadScopeValue(FrameValue.ScopeValue, RuleValue.OtherName)
    )
    PackedValue = (FlagsValue * 0x10000000 + CountValue) & 0xFFFFFFFF
    SignedValue = (
        PackedValue - 0x100000000 if PackedValue >= 0x80000000 else PackedValue
    )
    FrameValue.WriterValue.OutputValue.extend(EncodeScalar(SignedValue, "i32"))
    FrameValue.ScopeValue.ValuesValue[RuleValue.NameValue] = CountValue
