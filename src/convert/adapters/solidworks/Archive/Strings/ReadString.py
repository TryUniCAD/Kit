from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.ReadLength import ReadLength


# source encoding must survive decoding without consuming bytes beyond the string frame
def ReadString(BufferValue: bytes, OffsetValue: int) -> tuple[CStringValue, int]:
    UnitCount, NextOffset = ReadLength(BufferValue, OffsetValue)
    IsUnicode = UnitCount is None
    if IsUnicode:
        UnitCount, NextOffset = ReadLength(BufferValue, NextOffset)
    if UnitCount is None:
        raise ValueError("archive string repeats the Unicode marker")
    ByteCount = UnitCount * (2 if IsUnicode else 1)
    EndOffset = NextOffset + ByteCount
    if EndOffset > len(BufferValue):
        raise ValueError("archive string payload is truncated")
    PayloadValue = BufferValue[NextOffset:EndOffset]
    TextValue = (
        PayloadValue.decode("utf-16-le", "surrogatepass")
        if IsUnicode
        else PayloadValue.decode("latin-1")
    )
    return CStringValue(TextValue, IsUnicode), EndOffset
