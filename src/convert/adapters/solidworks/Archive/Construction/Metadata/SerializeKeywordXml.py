from typing import cast as CastValue
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import tostring as XmlBytes

from convert.adapters.base import ParseUntrusted


# the framed payload must remain well formed after the native lexical changes
def SerializeKeywordXml(RootValue: Element, CompactTags: bool) -> bytes:
    for NodeValue in RootValue.iter():
        TagValue = CastValue(object, NodeValue.tag)
        if TagValue is None or callable(TagValue):
            raise ValueError("native keyword framing requires named elements")
    try:
        PayloadValue: bytes = XmlBytes(
            RootValue, encoding="utf-8", short_empty_elements=True
        )
        PayloadValue = PayloadValue.replace(b"\r", b"&#13;")
        if CompactTags:
            PayloadValue = PayloadValue.replace(b" />", b"/>")
        Restored = ParseUntrusted(PayloadValue)
        if any(
            str(Source.tag) != Readback.tag
            or {str(Name) for Name in Source.attrib} != Readback.attrib.keys()
            for Source, Readback in zip(RootValue.iter(), Restored.iter(), strict=True)
        ):
            raise ValueError("serialized keyword names differ from the authored tree")
    except (SyntaxError, TypeError, ValueError) as ErrorInfo:
        raise ValueError(
            "native keyword framing requires well-formed XML"
        ) from ErrorInfo
    return PayloadValue
