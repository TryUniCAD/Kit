from builtins import setattr as SetAttrValue
from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)


# dimension xml must escape modeled names and format the actual finite value without sampled text or saved native content
def MakeKeyDimMut(ParentValue: Element, InputValue: KeywordDim) -> None:
    TextValue = (
        str(InputValue.NumberValue)
        if type(InputValue.NumberValue) is int
        else format(InputValue.NumberValue, ".17g")
    )
    if InputValue.UnitValue == "degree":
        TextValue += "°"
    SetAttrValue(
        SubElement(ParentValue, "Dimension", {"Name": InputValue.NameValue}),
        "text",
        TextValue,
    )
