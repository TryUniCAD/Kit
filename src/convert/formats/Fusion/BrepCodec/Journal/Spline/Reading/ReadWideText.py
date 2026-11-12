from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)


def ReadWideText(Cursor: FieldCursor) -> str:
    TagValue, Value = ReadFieldMut(Cursor)
    if TagValue not in (7, 8) or type(Value) is not str or not Value.isascii():
        raise ValueError("Invalid Fusion journal program text")
    if (TagValue == 8) != (len(Value) > 255):
        raise ValueError("Noncanonical Fusion journal text width")
    return Value
