from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyDimMut import (
    MakeKeyDimMut,
)


# feature xml must preserve the recovered conditional type and single child grammar without guessing unknown native tags
def MakeKeyFeatMut(RootValue: Element, InputValue: KeywordFeature) -> None:
    Attributes = {"id": str(InputValue.IdValue), "Name": InputValue.NameValue}
    if InputValue.KindValue is not None:
        Attributes["Type"] = InputValue.KindValue
    elif not (
        InputValue.TagValue == "Extrusion"
        and len(InputValue.ChildIds) == 1
        or InputValue.TagValue == "Sketch"
        and InputValue.Dissectable is True
    ):
        raise ValueError(
            "omitted keyword type requires a recovered cut or dissectable revolve sketch"
        )
    if InputValue.Dissectable is not None:
        Attributes["Dissectable"] = str(InputValue.Dissectable).lower()
    if InputValue.RootValue is not None:
        Attributes["DissectableRoot"] = str(InputValue.RootValue).lower()
    if InputValue.ChildIds:
        Attributes["DissectableChildren"] = ",".join(
            str(IdValue) for IdValue in InputValue.ChildIds
        )
    if (
        InputValue.TagValue == "Extrusion"
        and InputValue.KindValue is None
        and {DimValue.NameValue for DimValue in InputValue.DimensionValues} != {"D1"}
    ):
        raise ValueError("ordinary cut keyword requires its single driving dimension")
    FeatureValue = SubElement(RootValue, InputValue.TagValue, Attributes)
    for DimValue in InputValue.DimensionValues:
        if DimValue.UnitValue is not None and (
            InputValue.TagValue != "Feature" or InputValue.KindValue != "Revolve"
        ):
            raise ValueError(
                "keyword degree suffix requires an ordinary revolve feature"
            )
        MakeKeyDimMut(FeatureValue, DimValue)
