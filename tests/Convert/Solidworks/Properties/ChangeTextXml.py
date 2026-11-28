from copy import deepcopy as DeepCopy
from typing import cast as CastValue
from xml.etree.ElementTree import Element, tostring as WriteXml

from convert.adapters.base.SafeParsing import ParseUntrusted


# malformed property owners must travel through complete native archives before their public projection can be assessed
def ChangeTextXml(BufferValue: bytes, FaultValue: str) -> bytes:
    RootValue = ParseUntrusted(BufferValue)
    SectionValue = RootValue[1]
    ItemValue = next(
        Value for Value in SectionValue if Value.tag == "property" and Value.get("name")
    )
    if FaultValue in ("equation", "type"):
        ItemValue.set(
            "IsEquation" if FaultValue == "equation" else "TypeID",
            "True" if FaultValue == "equation" else "30",
        )
    elif FaultValue == "linked":
        setattr(ItemValue[0], "text", '$PRP:"Other"')
        setattr(ItemValue[1][0], "text", ItemValue[0].text)
    elif FaultValue == "evaluated":
        setattr(ItemValue[1][0], "text", "different resolved text")
    elif FaultValue == "dictionary":
        EntryValue = next(
            Value
            for Value in SectionValue
            if Value.tag == "propertyNameDictionaryElement" and Value.get("name")
        )
        EntryValue.set("pid", "999")
    elif FaultValue == "duplicate":
        ExtraValue = DeepCopy(ItemValue)
        ExtraValue.set("pid", "999")
        SectionValue.append(ExtraValue)
    elif FaultValue == "variant":
        setattr(ItemValue[0], "tag", ItemValue[0].tag.replace("lpstr", "i4"))
    elif FaultValue == "extra":
        SectionValue.append(Element("unqualifiedOwner"))
    else:
        raise ValueError("unknown property xml negative")
    return CastValue(bytes, WriteXml(RootValue, encoding="utf-8", xml_declaration=True))
