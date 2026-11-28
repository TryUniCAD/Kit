from convert.adapters.solidworks.Archive.Counts.CountField import (
    KCountShort,
    KCountLong,
    KCountWide,
    KCountLongMark,
    KCountWideMark,
    KCountWideMax,
)


# native count widths must follow model cardinality without saved payloads
def EncodeCount(CountValue: int, *, IsFramework: bool = False) -> bytes:
    if type(CountValue) is not int or type(IsFramework) is not bool:
        raise TypeError(
            "archive counts require an integer and an explicit boolean domain"
        )
    UpperLimit = KCountWideMax if IsFramework else KCountWideMark
    if not 0 <= CountValue <= UpperLimit:
        raise ValueError("archive count exceeds its unsigned domain")
    if CountValue < KCountLongMark:
        return KCountShort.pack(CountValue)
    if not IsFramework or CountValue < KCountWideMark:
        return KCountShort.pack(KCountLongMark) + KCountLong.pack(CountValue)
    return (
        KCountShort.pack(KCountLongMark)
        + KCountLong.pack(KCountWideMark)
        + KCountWide.pack(CountValue)
    )
