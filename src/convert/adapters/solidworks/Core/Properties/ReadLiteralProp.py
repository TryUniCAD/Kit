from xml.etree.ElementTree import Element

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.ReadPropRows import (
    ReadPropRows,
)
from convert.adapters.solidworks.Core.Properties.ReadPropVariant import ReadPropVariant


# named values qualify only when their literal and evaluated representations agree without links or equations
def ReadLiteralProp(ItemValue: Element, IsConfig: bool) -> tuple[str, str]:
    NamesValue = {"name", "pid", "IsEquation", "TypeID"}
    if (
        set(ItemValue.attrib) != NamesValue
        or ItemValue.get("IsEquation") != "False"
        or ItemValue.get("TypeID") != "0"
    ):
        raise ValueError("part property requires ordinary literal unlinked text")
    ChildrenValue = list(ItemValue)
    if len(ChildrenValue) not in ((1, 2) if IsConfig else (2,)):
        raise ValueError("part property has an unqualified evaluated value layout")
    TextValue = ReadPropVariant(ChildrenValue[0], "lpstr")
    if len(ChildrenValue) == 2:
        EvaluatedValue = ChildrenValue[1]
        if (
            EvaluatedValue.tag != "FPVals"
            or EvaluatedValue.attrib
            or len(EvaluatedValue) != 1
        ):
            raise ValueError("part property has an unsupported evaluated owner")
        if ReadPropVariant(EvaluatedValue[0], "lpstr") != TextValue:
            raise ValueError("part property evaluated value differs from its literal")
    return ReadPropRows({ItemValue.attrib["name"]: TextValue})[0]
