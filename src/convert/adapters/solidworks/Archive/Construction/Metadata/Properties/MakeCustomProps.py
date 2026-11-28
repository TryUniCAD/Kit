from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePropSection import (
    AddPropertyName,
    AddReservedProp,
    MakePropSection,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PropertyNames import (
    KConfigPropertyNamespace,
    KModelPropertyNamespace,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.WritePropXml import (
    WritePropXml,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.PropertyVocabulary import (
    KPropertyValueNamespace,
)


# the compatible text layout stores one raw value and an ordinary document value repeats as its evaluated text
def AddTextProperty(
    SectionValue: Element,
    IdentValue: int,
    NameValue: str,
    TextValue: str,
    IsConfiguration: bool,
) -> None:
    ItemValue = SubElement(
        SectionValue,
        "property",
        name=NameValue,
        pid=str(IdentValue),
        IsEquation="False",
        TypeID="0",
    )
    setattr(SubElement(ItemValue, "vt:lpstr"), "text", TextValue)
    if not IsConfiguration:
        ResultValues = SubElement(ItemValue, "FPVals")
        setattr(SubElement(ResultValues, "vt:lpstr"), "text", TextValue)


# ordinary custom property xml derives ids and reserved section state and the name dictionary from the selected scope
def MakeCustomProps(
    PropertyRows: tuple[tuple[str, str], ...], IsConfiguration: bool
) -> bytes:
    RootTag, RootNamespace = (
        ("ConfigProperties", KConfigPropertyNamespace)
        if IsConfiguration
        else ("Properties", KModelPropertyNamespace)
    )
    RootValue = Element(
        RootTag, {"xmlns": RootNamespace, "xmlns:vt": KPropertyValueNamespace}
    )
    SummarySection = MakePropSection(RootValue, False)
    if not IsConfiguration:
        AddReservedProp(SummarySection, 1, "i2", "65001")
        AddReservedProp(SummarySection, 22, "bool", "No")
    AddPropertyName(SummarySection, "", 0)
    UserSection = MakePropSection(RootValue, True)
    AddReservedProp(UserSection, 1, "i2", "65001")
    PropertyIds: dict[str, int] = {}
    for IdentValue, (NameValue, TextValue) in enumerate(PropertyRows, 3):
        AddTextProperty(UserSection, IdentValue, NameValue, TextValue, IsConfiguration)
        PropertyIds[NameValue] = IdentValue
    AddPropertyName(UserSection, "", 0)
    for NameValue in sorted(PropertyIds):
        AddPropertyName(UserSection, NameValue, PropertyIds[NameValue])
    return WritePropXml(RootValue)
