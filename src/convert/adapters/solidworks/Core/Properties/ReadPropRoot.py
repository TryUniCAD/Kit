from re import search as FindPattern
from xml.etree.ElementTree import Element

from convert.adapters.base.SafeParsing import ParseUntrusted


# the compatible utf8 profile must expose declarations to the shared doctype guard before xml interpretation
def ReadPropRoot(BufferValue: bytes) -> Element:
    TextValue = BufferValue.decode("utf-8-sig")
    if "\x00" in TextValue:
        raise ValueError("part property xml requires the compatible utf8 encoding")
    EncodingValue = FindPattern(
        r"""^\s*<\?xml\b[^?]*\bencoding\s*=\s*["']([^"']+)["']""", TextValue
    )
    if EncodingValue is not None and EncodingValue.group(1).casefold() not in (
        "utf-8",
        "utf8",
    ):
        raise ValueError("part property xml has an unsupported encoding declaration")
    return ParseUntrusted(TextValue)
