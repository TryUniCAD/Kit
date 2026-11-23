from collections.abc import Mapping
from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.InfoDictOrder import (
    KInfoDictOrder,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.InfoNames import (
    KInfoNames,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import (
    CheckPropText,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePropSection import (
    AddPropertyName,
)


# system information has its own variant tags and preserves an alias for each document text slot
def SetInfoRowsMut(
    SectionValue: Element, FieldsValue: Mapping[str, str | int | bool]
) -> None:
    KnownNames: set[str] = set(KInfoNames)
    if set(FieldsValue) != KnownNames:
        raise ValueError("assembly information requires the ordinary property roster")
    AddInfoPropMut(SectionValue, 1, "", "i2", "65001")
    for SlotValue, NameValue in enumerate(KInfoNames, 3):
        Value = FieldsValue[NameValue]
        if SlotValue < 18 and isinstance(Value, str):
            KindValue = "lpstr"
            TextValue = CheckPropText(Value) if Value else ""
        elif SlotValue == 19 and Value is False:
            KindValue = "bool"
            TextValue = "No"
        elif (
            SlotValue >= 18
            and SlotValue != 19
            and type(Value) is int
            and -(1 << 31) <= Value < 1 << 31
        ):
            KindValue = "i4"
            TextValue = str(Value)
        else:
            raise ValueError(
                "unsupported ordinary assembly information field " + NameValue
            )
        AddInfoPropMut(SectionValue, SlotValue, NameValue, KindValue, TextValue)
    AddPropertyName(SectionValue, "", 0)
    for SlotValue in KInfoDictOrder:
        NameValue = KInfoNames[SlotValue - 3]
        AddPropertyName(SectionValue, NameValue, SlotValue)
        if SlotValue < 18:
            NameAlias = f"{NameValue}({NameValue.removeprefix('SW-')})"
            AddPropertyName(SectionValue, NameAlias, SlotValue)


# the information property rows omit type id while retaining the actual lexical variant child
def AddInfoPropMut(
    SectionValue: Element,
    SlotValue: int,
    NameValue: str,
    KindValue: str,
    TextValue: str,
) -> None:
    PropertyValue = SubElement(
        SectionValue, "property", name=NameValue, pid=str(SlotValue)
    )
    setattr(SubElement(PropertyValue, "vt:" + KindValue), "text", TextValue)
