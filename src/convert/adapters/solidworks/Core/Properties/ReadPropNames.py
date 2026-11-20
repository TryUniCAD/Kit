from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Core.Properties.ReadPropId import ReadPropId


# lookup dictionaries must identify precisely the same named rows and the reserved unnamed entry
def ReadPropNames(SectionValue: Element) -> dict[str, int]:
    ResultValue: dict[str, int] = {}
    SeenNames: set[str] = set()
    for ItemValue in SectionValue:
        if ItemValue.tag != "propertyNameDictionaryElement":
            continue
        if (
            set(ItemValue.attrib) != {"name", "pid"}
            or len(ItemValue)
            or (ItemValue.text or "").strip()
        ):
            raise ValueError("part property dictionary has unclassified structure")
        NameValue = ItemValue.attrib["name"]
        if NameValue.casefold() in SeenNames:
            raise ValueError("part property dictionary repeats a name")
        SeenNames.add(NameValue.casefold())
        ResultValue[NameValue] = ReadPropId(ItemValue.get("pid"))
    return ResultValue
