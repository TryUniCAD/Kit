from typing import cast as CastValue
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import tostring as XmlBytes

from convert.adapters.base import ParseUntrusted


# the native boundary needs a named tree and well formed xml before lexical framing
def SerializeKeywordXml(RootValue: Element) -> bytes:
    for NodeValue in RootValue.iter():
        TagValue = CastValue(object, NodeValue.tag)
        if TagValue is None or callable(TagValue):
            raise ValueError("native keyword framing requires named elements")
    try:
        PayloadValue: bytes = XmlBytes(
            RootValue, encoding="utf-8", short_empty_elements=True
        )
        _ = ParseUntrusted(PayloadValue)
    except (SyntaxError, TypeError, ValueError) as ErrorInfo:
        raise ValueError(
            "native keyword framing requires well-formed XML"
        ) from ErrorInfo
    return PayloadValue
