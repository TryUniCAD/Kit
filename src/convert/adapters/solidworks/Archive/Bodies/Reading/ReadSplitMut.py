from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# split counts have independent framing and must preserve each word for equivalent writes
def ReadSplitMut(
    Cursor: BinaryReader, RuleValue: NativeField, CountName: str
) -> tuple[int, dict[str, int]]:
    HighValue = CastValue(int, ReadScalarMut(Cursor, "u32"))
    LowValue = CastValue(int, ReadScalarMut(Cursor, "u32"))
    CountValue = (HighValue << 32) | LowValue
    if RuleValue.ModeValue == "Combined":
        return NormalizeCount(CountValue, ""), {CountName: CountValue}
    return NormalizeCount(CountValue, RuleValue.ModeValue), {
        CountName: HighValue,
        RuleValue.OtherName: LowValue,
    }
