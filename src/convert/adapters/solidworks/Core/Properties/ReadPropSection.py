from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.ReadPropRows import (
    ReadPropRows,
)
from convert.adapters.solidworks.Core.Properties.ReadLiteralProp import ReadLiteralProp
from convert.adapters.solidworks.Core.Properties.ReadPropId import ReadPropId
from convert.adapters.solidworks.Core.Properties.ReadPropNames import ReadPropNames
from convert.adapters.solidworks.Core.Properties.ReadReserved import ReadReserved
from convert.adapters.solidworks.Core.Properties.CheckPropBag import (
    CheckPropBag,
)


# section admission verifies reserved ownership and dictionary bijection before returning any authored values
def ReadPropSection(
    SectionValue: Element, IsConfig: bool, IsUser: bool
) -> dict[str, str]:
    ReservedValues: dict[int, tuple[str, str]] = {}
    ResultValue: dict[str, str] = {}
    NamesValue = {"": 0}
    SeenNames: set[str] = set()
    SeenIds: set[int] = set()
    for ItemValue in SectionValue:
        if ItemValue.tag == "propertyNameDictionaryElement":
            continue
        if ItemValue.tag != "property":
            raise ValueError("part property section contains an unqualified child")
        IdentValue = ReadPropId(ItemValue.get("pid"))
        if IdentValue in SeenIds:
            raise ValueError("part property section repeats a value identifier")
        SeenIds.add(IdentValue)
        if ItemValue.get("name") == "":
            ReservedValues[IdentValue] = ReadReserved(ItemValue)[1]
        else:
            if not IsUser or IdentValue < 3 or len(ResultValue) >= 4096:
                raise ValueError("part property has an unsupported named owner")
            NameValue, TextValue = ReadLiteralProp(ItemValue, IsConfig)
            if NameValue.casefold() in SeenNames:
                raise ValueError("part property section repeats a value name")
            SeenNames.add(NameValue.casefold())
            ResultValue[NameValue], NamesValue[NameValue] = TextValue, IdentValue
    CheckPropBag(
        ReservedValues, ReadPropNames(SectionValue), NamesValue, IsConfig, IsUser
    )
    return dict(ReadPropRows(ResultValue))
