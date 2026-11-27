from convert.adapters.solidworks.Archive.Counts.CountField import (
    KCountShort,
    KCountLong,
    KCountWide,
    KCountLongMark,
    KCountWideMark,
)


# native count domains need independent decoding before collection allocation
def ReadCount(
    BufferValue: bytes,
    OffsetValue: int,
    *,
    IsFramework: bool = False,
    LimitValue: int | None = None,
) -> tuple[int, int]:
    if type(BufferValue) is not bytes:
        raise TypeError("archive count input must be bytes")
    if type(OffsetValue) is not int or type(IsFramework) is not bool:
        raise TypeError("archive count position and domain have invalid types")
    EndValue = len(BufferValue) if LimitValue is None else LimitValue
    if OffsetValue < 0 or not OffsetValue + KCountShort.size <= EndValue <= len(
        BufferValue
    ):
        raise ValueError("archive count has no complete unsigned short")
    CountValue = int(KCountShort.unpack_from(BufferValue, OffsetValue)[0])
    NextOffset = OffsetValue + KCountShort.size
    if CountValue == KCountLongMark:
        if NextOffset + KCountLong.size > EndValue:
            raise ValueError("archive count has no complete unsigned long")
        CountValue = int(KCountLong.unpack_from(BufferValue, NextOffset)[0])
        NextOffset += KCountLong.size
        if IsFramework and CountValue == KCountWideMark:
            if NextOffset + KCountWide.size > EndValue:
                raise ValueError("framework count has no complete unsigned long long")
            CountValue = int(KCountWide.unpack_from(BufferValue, NextOffset)[0])
            NextOffset += KCountWide.size
    return CountValue, NextOffset
