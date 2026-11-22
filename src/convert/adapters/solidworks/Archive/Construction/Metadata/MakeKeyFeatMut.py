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
        and InputValue.DimensionValues
        and {DimValue.NameValue for DimValue in InputValue.DimensionValues} != {"D1"}
    ):
        raise ValueError(
            "ordinary cut keyword permits no driver or its actual single D1 dimension"
        )
    if InputValue.KindValue == "Revolve" and (
        InputValue.TagValue != "Feature"
        or tuple(
            (DimValue.NameValue, DimValue.UnitValue)
            for DimValue in InputValue.DimensionValues
        )
        not in (
            (("D1", "degree"),),
            (("D1", "degree"), ("D2", "degree")),
            (("D2", "degree"), ("D1", "degree")),
        )
    ):
        raise ValueError(
            "ordinary revolve keywords require active D1 and optional D2 degree drivers"
        )
    FeatureValue = SubElement(RootValue, InputValue.TagValue, Attributes)
    for DimValue in InputValue.DimensionValues:
        if DimValue.UnitValue is not None and InputValue.KindValue != "Revolve":
            raise ValueError(
                "keyword degree suffix requires an ordinary revolve feature"
            )
        MakeKeyDimMut(FeatureValue, DimValue)
