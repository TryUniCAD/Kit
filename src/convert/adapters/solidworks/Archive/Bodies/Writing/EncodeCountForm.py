from struct import pack as PackValue

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount


# equivalent source counts may require a length beyond the canonical emitted form
def EncodeCountForm(
    CountValue: object, WidthValue: object, *, IsFramework: bool
) -> bytes:
    if type(CountValue) is not int or type(WidthValue) is not int:
        raise ValueError("archive count width requires an integer count and width")
    Canonical = EncodeCount(CountValue, IsFramework=IsFramework)
    if WidthValue == len(Canonical):
        return Canonical
    if WidthValue == 6 and len(Canonical) == 2:
        return PackValue("<HI", 0xFFFF, CountValue)
    if WidthValue == 14 and IsFramework:
        return PackValue("<HIQ", 0xFFFF, 0xFFFFFFFF, CountValue)
    raise ValueError("archive count width conflicts with its value or domain")
