from struct import pack as PackValue
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# native strings must derive every header and payload byte from supplied text
def EncodeString(StringValue: CStringValue, *, IsSourceFrame: bool = False) -> bytes:
    if type(StringValue) is not CStringValue or type(IsSourceFrame) is not bool:
        raise TypeError(
            "archive string encoding requires typed text and a boolean mode"
        )
    if not IsSourceFrame and not StringValue.IsUnicode:
        raise ValueError("native wide string output requires Unicode text")
    try:
        PayloadValue = (
            StringValue.TextValue.encode("utf-16-le", "surrogatepass")
            if StringValue.IsUnicode
            else StringValue.TextValue.encode("latin-1")
        )
    except UnicodeEncodeError:
        raise ValueError("archive ANSI text is outside the byte domain") from None
    UnitCount = len(PayloadValue) // 2 if StringValue.IsUnicode else len(PayloadValue)
    if UnitCount > 0x7FFFFFFF:
        raise ValueError("archive string length exceeds the signed CString domain")
    if UnitCount < 0xFF:
        LengthValue = PackValue("<B", UnitCount)
    elif UnitCount < 0xFFFE:
        LengthValue = PackValue("<BH", 0xFF, UnitCount)
    else:
        LengthValue = PackValue("<BHI", 0xFF, 0xFFFF, UnitCount)
    PrefixValue = PackValue("<BH", 0xFF, 0xFFFE) if StringValue.IsUnicode else b""
    return PrefixValue + LengthValue + PayloadValue
