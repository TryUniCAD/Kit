from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.BindXmlScopeMut import (
    BindXmlScopeMut,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ExpandXmlName import (
    ExpandXmlName,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HasXmlAttrs import (
    HasXmlAttrs,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.ReadXmlScopes import (
    KXmlScopes,
)


# authored and parsed namespace bindings each follow the same tree paths before comparing qualified names
def CheckXmlTree(
    SourceValue: Element,
    ParsedValue: Element,
    AuthoredScope: dict[str, str],
    ParsedScope: dict[str, str],
    ParsedScopes: KXmlScopes,
) -> None:
    Attributes = {
        str(NameValue): Value for NameValue, Value in SourceValue.attrib.items()
    }
    Declarations = {
        NameValue: Value
        for NameValue, Value in Attributes.items()
        if NameValue == "xmlns" or NameValue.startswith("xmlns:")
    }
    Explicit = {
        "" if NameValue == "xmlns" else NameValue.removeprefix("xmlns:"): Value
        for NameValue, Value in Declarations.items()
    }
    with (
        BindXmlScopeMut(AuthoredScope, Explicit),
        BindXmlScopeMut(ParsedScope, ParsedScopes.get(ParsedValue, {})),
    ):
        Expected = {
            ExpandXmlName(NameValue, AuthoredScope, False): Value
            for NameValue, Value in Attributes.items()
            if NameValue not in Declarations
        }
        if (
            ExpandXmlName(str(SourceValue.tag), AuthoredScope, True) != ParsedValue.tag
            or not HasXmlAttrs(Expected, ParsedValue.attrib, ParsedScope)
            or (SourceValue.text or "") != (ParsedValue.text or "")
            or (SourceValue.tail or "") != (ParsedValue.tail or "")
            or len(SourceValue) != len(ParsedValue)
        ):
            raise ValueError("serialized keyword tree differs from the authored tree")
        for Source, Parsed in zip(SourceValue, ParsedValue, strict=True):
            CheckXmlTree(Source, Parsed, AuthoredScope, ParsedScope, ParsedScopes)
