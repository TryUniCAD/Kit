from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.SelectCountWord import (
    SelectCountWord,
)
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# stored split words must describe actual unsigned wire values before retention
def PackCountWords(HighValue: object, LowValue: object) -> int | None:
    if type(HighValue) is not int or type(LowValue) is not int:
        return None
    if not 0 <= HighValue <= 0xFFFFFFFF or not 0 <= LowValue <= 0xFFFFFFFF:
        return None
    return (HighValue << 32) | LowValue


# masked split counts must retain both words when the interpreted count agrees
def WriteSplitMut(
    FrameValue: WriteFrame, RuleValue: NativeField, CountName: str, ItemCount: int
) -> None:
    Fields = FrameValue.ScopeValue.FieldsValue
    if RuleValue.ModeValue == "Combined":
        CountValue = SelectCountWord(Fields.get(CountName), ItemCount, "")
    else:
        WireValue = PackCountWords(
            Fields.get(CountName), Fields.get(RuleValue.OtherName)
        )
        CountValue = SelectCountWord(WireValue, ItemCount, RuleValue.ModeValue)
    HighValue = CountValue >> 32
    LowValue = CountValue & 0xFFFFFFFF
    Buffer = FrameValue.WriterValue.OutputValue
    Buffer.extend(EncodeScalar(HighValue, "u32") + EncodeScalar(LowValue, "u32"))
    Values = FrameValue.ScopeValue.ValuesValue
    if RuleValue.ModeValue == "Combined":
        Values[CountName] = CountValue
    else:
        Values[CountName], Values[RuleValue.OtherName] = HighValue, LowValue
