from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Core.Properties.ReadPropId import ReadPropId
from convert.adapters.solidworks.Core.Properties.ReadPropVariant import ReadPropVariant


# reserved entries carry typed codepage and hyperlink state rather than authored custom text
def ReadReserved(ItemValue: Element) -> tuple[int, tuple[str, str]]:
    if (
        ItemValue.attrib != {"name": "", "pid": ItemValue.get("pid"), "TypeID": "0"}
        or len(ItemValue) != 1
    ):
        raise ValueError("part property reserved entry has unsupported attributes")
    IdentValue = ReadPropId(ItemValue.get("pid"))
    TypeValue = {1: "i2", 22: "bool"}.get(IdentValue)
    if TypeValue is None:
        raise ValueError("part property has an unqualified reserved identifier")
    return IdentValue, (TypeValue, ReadPropVariant(ItemValue[0], TypeValue))
