from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.CheckXmlNames import (
    CheckXmlNames,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.CheckXmlTree import (
    CheckXmlTree,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ReadXmlScopes import (
    KXmlNamespace,
    ReadXmlScopes,
)
from convert.adapters.solidworks.Core.Native import XmlTree


# the framed payload must remain well formed after the native lexical changes
def EmitKeywordXml(RootValue: Element, CompactTags: bool) -> bytes:
    CheckXmlNames(RootValue)
    try:
        PayloadValue = XmlTree.tostring(
            RootValue, encoding="utf-8", short_empty_elements=True
        )
        PayloadValue = PayloadValue.replace(b"\r", b"&#13;")
        if CompactTags:
            PayloadValue = PayloadValue.replace(b" />", b"/>")
        ParsedValue, ParsedScopes = ReadXmlScopes(PayloadValue)
        if ParsedValue.tag != RootValue.tag:
            raise ValueError("serialized keyword root changed its native name")
        CheckXmlTree(
            RootValue,
            ParsedValue,
            {"xml": KXmlNamespace},
            {"xml": KXmlNamespace},
            ParsedScopes,
        )
    except (SyntaxError, TypeError, ValueError) as ErrorInfo:
        raise ValueError(
            "native keyword framing requires well-formed XML"
        ) from ErrorInfo
    return PayloadValue
