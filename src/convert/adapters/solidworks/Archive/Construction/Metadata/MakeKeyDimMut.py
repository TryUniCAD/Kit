from builtins import setattr as SetAttrValue
from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)


# dimension xml must escape modeled names and format the actual finite value without sampled text or saved native content
def MakeKeyDimMut(ParentValue: Element, InputValue: KeywordDim) -> None:
    NumberValue = InputValue.NumberValue
    PlacesValue = InputValue.PlacesValue
    if type(NumberValue) is int:
        TextValue = str(NumberValue)
        if PlacesValue:
            TextValue += "." + "0" * PlacesValue
    else:
        TextValue = format(
            NumberValue, ".17g" if PlacesValue is None else f".{PlacesValue}f"
        )
    if InputValue.PrefixValue is not None:
        TextValue = (
            "R" if InputValue.PrefixValue == "radius" else "<MOD-DIAM>"
        ) + TextValue
    if InputValue.UnitValue == "degree":
        TextValue += "°"
    SetAttrValue(
        SubElement(ParentValue, "Dimension", {"Name": InputValue.NameValue}),
        "text",
        TextValue,
    )
