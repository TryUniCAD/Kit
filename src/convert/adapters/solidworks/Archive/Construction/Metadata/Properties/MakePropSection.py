from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import (
    KSummaryPropertyFormat,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import (
    KUserPropertyFormat,
)


# reserved entries are typed ole identifiers with no authored property name
def AddReservedProp(
    SectionValue: Element, IdentValue: int, VariantTag: str, TextValue: str
) -> None:
    ItemValue = SubElement(
        SectionValue, "property", name="", pid=str(IdentValue), TypeID="0"
    )
    setattr(SubElement(ItemValue, "vt:" + VariantTag), "text", TextValue)


# each bag indexes names separately from the property value row and uses their exact computed identifiers
def AddPropertyName(SectionValue: Element, NameValue: str, IdentValue: int) -> None:
    _ = SubElement(
        SectionValue,
        "propertyNameDictionaryElement",
        name=NameValue,
        pid=str(IdentValue),
    )


# the section names use the standard property set guid and are outside the surrounding xml namespace
def MakePropSection(RootValue: Element, IsUserSection: bool) -> Element:
    SectionName, FormatValue = (
        ("UserDefinedProperties", KUserPropertyFormat)
        if IsUserSection
        else ("DocumentSummaryInformation", KSummaryPropertyFormat)
    )
    return SubElement(
        RootValue,
        "propertySection",
        {"xmlns": "", "name": SectionName, "fmtid": FormatValue},
    )
