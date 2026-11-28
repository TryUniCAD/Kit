from convert.adapters.solidworks.Archive.Strings.StringField import (
    KTextByte,
    KTextWord,
    KTextLong,
    KTextWordMark,
    KTextWideMark,
    KTextLongMark,
    KTextLengthMax,
)


# string framing needs its own markers before text encoding determines payload size
def ReadLength(
    BufferValue: bytes, OffsetValue: int, *, LimitValue: int | None = None
) -> tuple[int | None, int]:
    if type(BufferValue) is not bytes:
        raise TypeError("archive string input must be bytes")
    if type(OffsetValue) is not int:
        raise TypeError("archive string position must be an integer")
    EndValue = len(BufferValue) if LimitValue is None else LimitValue
    if not 0 <= OffsetValue < EndValue <= len(BufferValue):
        raise ValueError("archive string has no complete length byte")
    UnitCount = BufferValue[OffsetValue]
    NextOffset = OffsetValue + KTextByte.size
    if UnitCount == KTextWordMark:
        if NextOffset + KTextWord.size > EndValue:
            raise ValueError("archive string has no complete length word")
        UnitCount = int(KTextWord.unpack_from(BufferValue, NextOffset)[0])
        NextOffset += KTextWord.size
        if UnitCount == KTextWideMark:
            return None, NextOffset
        if UnitCount == KTextLongMark:
            if NextOffset + KTextLong.size > EndValue:
                raise ValueError("archive string has no complete length double word")
            UnitCount = int(KTextLong.unpack_from(BufferValue, NextOffset)[0])
            NextOffset += KTextLong.size
            if UnitCount == 0xFFFFFFFF:
                raise ValueError("archive string has a reserved double word length")
    if UnitCount > KTextLengthMax:
        raise ValueError("archive string length exceeds the signed CString domain")
    return UnitCount, NextOffset
