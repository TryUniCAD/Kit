from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.ReadLength import ReadLength

from convert.adapters.solidworks.Archive.Strings.StringField import (
    KWideEncoding,
    KWideErrors,
    KByteEncoding,
    KWideUnitBytes,
)


# source encoding must survive decoding without consuming bytes beyond the string frame
def ReadString(
    BufferValue: bytes, OffsetValue: int, *, LimitValue: int | None = None
) -> tuple[CStringValue, int]:
    UnitCount, NextOffset = ReadLength(BufferValue, OffsetValue, LimitValue=LimitValue)
    IsUnicode = UnitCount is None
    if IsUnicode:
        UnitCount, NextOffset = ReadLength(
            BufferValue, NextOffset, LimitValue=LimitValue
        )
    if UnitCount is None:
        raise ValueError("archive string repeats the Unicode marker")
    ByteCount = UnitCount * (KWideUnitBytes if IsUnicode else 1)
    EndOffset = NextOffset + ByteCount
    if EndOffset > (len(BufferValue) if LimitValue is None else LimitValue):
        raise ValueError("archive string payload is truncated")
    PayloadValue = BufferValue[NextOffset:EndOffset]
    TextValue = (
        PayloadValue.decode(KWideEncoding, KWideErrors)
        if IsUnicode
        else PayloadValue.decode(KByteEncoding)
    )
    return CStringValue(TextValue, IsUnicode), EndOffset
