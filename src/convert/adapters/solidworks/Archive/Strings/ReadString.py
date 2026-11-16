from struct import unpack_from as UnpackValue
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# source encoding must survive decoding without consuming bytes beyond the string frame
def ReadString(BufferValue: bytes, OffsetValue: int) -> tuple[CStringValue, int]:
    if type(BufferValue) is not bytes:
        raise TypeError("archive string input must be bytes")
    if type(OffsetValue) is not int:
        raise TypeError("archive string position must be an integer")
    if OffsetValue < 0 or OffsetValue >= len(BufferValue):
        raise ValueError("archive string has no complete length byte")
    UnitCount = BufferValue[OffsetValue]
    NextOffset = OffsetValue + 1
    IsUnicode = False
    if UnitCount == 0xFF:
        if NextOffset + 2 > len(BufferValue):
            raise ValueError("archive string has no complete length word")
        UnitCount = int(UnpackValue("<H", BufferValue, NextOffset)[0])
        NextOffset += 2
        if UnitCount == 0xFFFE:
            IsUnicode = True
            if NextOffset >= len(BufferValue):
                raise ValueError("archive Unicode string has no complete length byte")
            UnitCount = BufferValue[NextOffset]
            NextOffset += 1
            if UnitCount == 0xFF:
                if NextOffset + 2 > len(BufferValue):
                    raise ValueError(
                        "archive Unicode string has no complete length word"
                    )
                UnitCount = int(UnpackValue("<H", BufferValue, NextOffset)[0])
                NextOffset += 2
                if UnitCount == 0xFFFE:
                    raise ValueError("archive string repeats the Unicode marker")
        if UnitCount == 0xFFFF:
            if NextOffset + 4 > len(BufferValue):
                raise ValueError("archive string has no complete length double word")
            UnitCount = int(UnpackValue("<I", BufferValue, NextOffset)[0])
            NextOffset += 4
            if UnitCount == 0xFFFFFFFF:
                raise ValueError("archive string has a reserved double word length")
    if UnitCount > 0x7FFFFFFF:
        raise ValueError("archive string length exceeds the signed CString domain")
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
