from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import ParseXml

# drawing properties use the native package namespace to separate system values
KDrawPropNamespace = "{http://schemas.openxmlformats.org/officeDocument/2006/SolidworksInformation-properties}"

# native property text is distinguished from the parallel property dictionary
KPropertyTextTag = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}lpstr"
)


# property parsing must preserve only the unique nonempty values needed by layout
def ReadDrawProps(DataValue: bytes, Names: frozenset[str]) -> dict[str, str]:
    RootValue = ParseXml(DataValue)
    if RootValue.tag != KDrawPropNamespace + "Properties":
        raise SldprtFormat("drawing information namespace is unsupported")
    Values: dict[str, str] = {}
    for Property in RootValue.iter("property"):
        NameValue = Property.get("name", "")
        if NameValue not in Names:
            continue
        Items = Property.findall(KPropertyTextTag)
        if len(Items) != 1 or Items[0].text is None or not Items[0].text.strip():
            raise SldprtFormat(f"drawing information has invalid {NameValue} text")
        if NameValue in Values:
            raise SldprtFormat(f"drawing information repeats {NameValue}")
        Values[NameValue] = Items[0].text.strip()
    if Values.keys() != Names:
        raise SldprtFormat("drawing information is missing layout properties")
    return Values
