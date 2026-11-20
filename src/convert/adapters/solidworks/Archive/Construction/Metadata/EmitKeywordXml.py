from xml.etree.ElementTree import Element

from defusedxml.ElementTree import tostring as XmlBytes

from convert.adapters.base import ParseUntrusted
from convert.adapters.solidworks.Archive.Construction.Metadata.CheckXmlNames import (
    CheckXmlNames,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.CheckXmlTree import (
    CheckXmlTree,
)


# the framed payload must remain well formed after the native lexical changes
def EmitKeywordXml(RootValue: Element, CompactTags: bool) -> bytes:
    CheckXmlNames(RootValue)
    try:
        PayloadValue: bytes = XmlBytes(
            RootValue, encoding="utf-8", short_empty_elements=True
        )
        PayloadValue = PayloadValue.replace(b"\r", b"&#13;")
        if CompactTags:
            PayloadValue = PayloadValue.replace(b" />", b"/>")
        ParsedValue = ParseUntrusted(PayloadValue)
        if ParsedValue.tag != RootValue.tag:
            raise ValueError("serialized keyword root changed its native name")
        CheckXmlTree(
            RootValue, ParsedValue, {"xml": "http://www.w3.org/XML/1998/namespace"}
        )
    except (SyntaxError, TypeError, ValueError) as ErrorInfo:
        raise ValueError(
            "native keyword framing requires well-formed XML"
        ) from ErrorInfo
    return PayloadValue
