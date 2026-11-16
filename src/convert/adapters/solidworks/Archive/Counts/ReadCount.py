from struct import unpack_from as UnpackValue


# native count domains need independent decoding before collection allocation
def ReadCount(
    BufferValue: bytes, OffsetValue: int, *, IsFramework: bool = False
) -> tuple[int, int]:
    if not isinstance(BufferValue, bytes):
        raise TypeError("archive count input must be bytes")
    if type(OffsetValue) is not int or type(IsFramework) is not bool:
        raise TypeError("archive count position and domain have invalid types")
    if OffsetValue < 0 or OffsetValue + 2 > len(BufferValue):
        raise ValueError("archive count has no complete unsigned short")
    CountValue = int(UnpackValue("<H", BufferValue, OffsetValue)[0])
    NextOffset = OffsetValue + 2
    if CountValue == 0xFFFF:
        if NextOffset + 4 > len(BufferValue):
            raise ValueError("archive count has no complete unsigned long")
        CountValue = int(UnpackValue("<I", BufferValue, NextOffset)[0])
        NextOffset += 4
        if IsFramework and CountValue == 0xFFFFFFFF:
            if NextOffset + 8 > len(BufferValue):
                raise ValueError("framework count has no complete unsigned long long")
            CountValue = int(UnpackValue("<Q", BufferValue, NextOffset)[0])
            NextOffset += 8
    return CountValue, NextOffset
