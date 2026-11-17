from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# ghost identifiers pack flags and repetition length into one signed native word
def ReadGhostMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    PackedValue = CastValue(int, ReadScalarMut(FrameValue.ReaderValue.Cursor, "i32"))
    FlagsValue = PackedValue >> 28
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.OtherName] = FlagsValue
    Fields[RuleValue.NameValue] = PackedValue - FlagsValue * 0x10000000
