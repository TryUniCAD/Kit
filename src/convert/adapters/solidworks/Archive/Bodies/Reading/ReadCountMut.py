from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# array prefixes retain their native words while item traversal uses the proven count rule
def ReadCountMut(FrameValue: ReadFrame, RuleValue: NativeField) -> int:
    Cursor = FrameValue.ReaderValue.Cursor
    Fields = FrameValue.ScopeValue.FieldsValue
    CountName = RuleValue.CountValue or RuleValue.NameValue + "#count"
    if RuleValue.TypeValue in ("Count", "Framework"):
        CountValue, Offset = ReadCount(
            Cursor.BytesValue,
            Cursor.OffsetValue,
            IsFramework=RuleValue.TypeValue == "Framework",
        )
        Cursor.OffsetValue = Offset
    elif RuleValue.TypeValue == "Split":
        HighValue = CastValue(int, ReadScalarMut(Cursor, "u32"))
        LowValue = CastValue(int, ReadScalarMut(Cursor, "u32"))
        if RuleValue.ModeValue == "Combined":
            Fields[CountName] = (HighValue << 32) | LowValue
            return NormalizeCount((HighValue << 32) | LowValue, "")
        Fields[CountName], Fields[RuleValue.OtherName] = HighValue, LowValue
        return NormalizeCount((HighValue << 32) | LowValue, RuleValue.ModeValue)
    else:
        CountValue = CastValue(int, ReadScalarMut(Cursor, RuleValue.TypeValue))
    Fields[CountName] = CountValue
    return NormalizeCount(CountValue, RuleValue.ModeValue)
