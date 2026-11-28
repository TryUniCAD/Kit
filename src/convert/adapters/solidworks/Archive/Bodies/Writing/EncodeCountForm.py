from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount

from convert.adapters.solidworks.Archive.Counts.CountField import (
    KCountShort,
    KCountLong,
    KCountWide,
    KCountLongMark,
    KCountWideMark,
)


# equivalent source counts may require a length beyond the canonical emitted form
def EncodeCountForm(
    CountValue: object, WidthValue: object, *, IsFramework: bool
) -> bytes:
    if type(CountValue) is not int or type(WidthValue) is not int:
        raise ValueError("archive count width requires an integer count and width")
    Canonical = EncodeCount(CountValue, IsFramework=IsFramework)
    if WidthValue == len(Canonical):
        return Canonical
    if (
        WidthValue == KCountShort.size + KCountLong.size
        and len(Canonical) == KCountShort.size
    ):
        return KCountShort.pack(KCountLongMark) + KCountLong.pack(CountValue)
    if (
        WidthValue == KCountShort.size + KCountLong.size + KCountWide.size
        and IsFramework
    ):
        return (
            KCountShort.pack(KCountLongMark)
            + KCountLong.pack(KCountWideMark)
            + KCountWide.pack(CountValue)
        )
    raise ValueError("archive count width conflicts with its value or domain")
