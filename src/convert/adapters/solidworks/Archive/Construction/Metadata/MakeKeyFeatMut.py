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
        != (("D1", "degree"),)
    ):
        raise ValueError(
            "ordinary revolve keyword requires its single D1 degree driver"
        )
    if InputValue.KindValue == "Revolve-Thin" and (
        InputValue.TagValue != "Feature"
        or tuple(
            (DimValue.NameValue, DimValue.UnitValue)
            for DimValue in InputValue.DimensionValues
        )
        not in (
            (("D3", None), ("D1", "degree")),
            (("D1", "degree"), ("D4", None), ("D3", None)),
        )
    ):
        raise ValueError(
            "thin revolve keyword requires its active angle and wall drivers"
        )
    FeatureValue = SubElement(RootValue, InputValue.TagValue, Attributes)
    for DimValue in InputValue.DimensionValues:
        if DimValue.UnitValue is not None and InputValue.KindValue not in (
            "Revolve",
            "Revolve-Thin",
        ):
            raise ValueError("keyword degree suffix requires a revolve feature")
        MakeKeyDimMut(FeatureValue, DimValue)
