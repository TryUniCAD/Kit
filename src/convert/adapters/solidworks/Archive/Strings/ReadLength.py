from struct import unpack_from as UnpackValue


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
    NextOffset = OffsetValue + 1
    if UnitCount == 0xFF:
        if NextOffset + 2 > EndValue:
            raise ValueError("archive string has no complete length word")
        UnitCount = int(UnpackValue("<H", BufferValue, NextOffset)[0])
        NextOffset += 2
        if UnitCount == 0xFFFE:
            return None, NextOffset
        if UnitCount == 0xFFFF:
            if NextOffset + 4 > EndValue:
                raise ValueError("archive string has no complete length double word")
            UnitCount = int(UnpackValue("<I", BufferValue, NextOffset)[0])
            NextOffset += 4
            if UnitCount == 0xFFFFFFFF:
                raise ValueError("archive string has a reserved double word length")
    if UnitCount > 0x7FFFFFFF:
        raise ValueError("archive string length exceeds the signed CString domain")
    return UnitCount, NextOffset
