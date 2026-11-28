from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue

from convert.adapters.solidworks.Archive.Strings.StringField import (
    KTextByte,
    KTextWord,
    KTextLong,
    KTextWordMark,
    KTextWideMark,
    KTextLongMark,
    KTextLengthMax,
    KWideEncoding,
    KWideErrors,
    KByteEncoding,
    KWideUnitBytes,
)


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
            StringValue.TextValue.encode(KWideEncoding, KWideErrors)
            if StringValue.IsUnicode
            else StringValue.TextValue.encode(KByteEncoding)
        )
    except UnicodeEncodeError:
        raise ValueError("archive ANSI text is outside the byte domain") from None
    UnitCount = (
        len(PayloadValue) // KWideUnitBytes
        if StringValue.IsUnicode
        else len(PayloadValue)
    )
    if UnitCount > KTextLengthMax:
        raise ValueError("archive string length exceeds the signed CString domain")
    if UnitCount < KTextWordMark:
        LengthValue = KTextByte.pack(UnitCount)
    elif UnitCount < KTextWideMark:
        LengthValue = KTextByte.pack(KTextWordMark) + KTextWord.pack(UnitCount)
    else:
        LengthValue = (
            KTextByte.pack(KTextWordMark)
            + KTextWord.pack(KTextLongMark)
            + KTextLong.pack(UnitCount)
        )
    PrefixValue = (
        (KTextByte.pack(KTextWordMark) + KTextWord.pack(KTextWideMark))
        if StringValue.IsUnicode
        else b""
    )
    return PrefixValue + LengthValue + PayloadValue
