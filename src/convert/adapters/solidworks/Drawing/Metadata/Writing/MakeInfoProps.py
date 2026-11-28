from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import (
    KInformationNamespace,
    KPropertyValueNamespace,
    KUserPropertyFormat,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.WriteDrawingXml import (
    WriteDrawingXml,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.XmlTextValue import (
    XmlTextValue,
)


# ordinary text property ids dictionary entries and lexical namespaces must derive from the actual ordered metadata values
def MakeInfoProps(ValuesValue: tuple[tuple[str, str], ...]) -> bytes:
    if type(ValuesValue) is not tuple or len(ValuesValue) + 2 >= 16777216:
        raise ValueError(
            "drawing metadata property rows exceed the ordinary typed domain"
        )
    NamesValue = tuple(XmlTextValue(RowValue[0], False) for RowValue in ValuesValue)
    if len(set(NamesValue)) != len(NamesValue):
        raise ValueError("drawing metadata property names must be distinct")
    RootValue = Element(
        "ns0:Properties",
        {"xmlns:ns0": KInformationNamespace, "xmlns:vt": KPropertyValueNamespace},
    )
    SectionValue = SubElement(
        RootValue,
        "propertySection",
        name="UserDefinedProperties",
        fmtid=KUserPropertyFormat,
    )
    for Identifier, (NameValue, TextValue) in enumerate(ValuesValue, 3):
        ItemValue = SubElement(
            SectionValue, "property", name=NameValue, pid=str(Identifier)
        )
        setattr(
            SubElement(ItemValue, "vt:lpstr"), "text", XmlTextValue(TextValue, True)
        )
    for Identifier, NameValue in enumerate(NamesValue, 3):
        _ = SubElement(
            SectionValue,
            "propertyNameDictionaryElement",
            name=NameValue,
            pid=str(Identifier),
        )
    return WriteDrawingXml(RootValue)
