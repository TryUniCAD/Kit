from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Strings.ReadLength import ReadLength


# canonical body text must retain its wire identity without allocating a second payload
def ReadBodyTextMut(Cursor: BinaryReader) -> str | tuple[str, str]:
    CountStart = Cursor.OffsetValue
    CountValue, NextOffset = ReadLength(
        Cursor.BytesValue, CountStart, LimitValue=Cursor.LimitValue
    )
    if CountValue is None:
        CountStart = NextOffset
        CountValue, NextOffset = ReadLength(
            Cursor.BytesValue, CountStart, LimitValue=Cursor.LimitValue
        )
    if CountValue is None:
        raise ValueError("archive string repeats the Unicode marker")
    WidthValue = 1 if CountValue < 0xFF else 3
    if CountValue >= 0xFFFE:
        WidthValue = 7
    if NextOffset - CountStart != WidthValue:
        raise ValueError("SOLIDWORKS body text has a noncanonical length prefix")
    TextValue = ReadCStringMut(Cursor)
    if TextValue.IsUnicode:
        return TextValue.TextValue
    return "A", TextValue.TextValue
