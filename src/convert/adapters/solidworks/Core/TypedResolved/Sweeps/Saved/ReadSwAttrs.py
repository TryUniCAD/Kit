from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)


# typed real values must retain their native attribute definition and body ownership
def ReadSwReals(
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
    NameValue: str,
    CountValue: int,
) -> tuple[float, ...]:
    Attribute = Attributes[NameValue]
    Definition = RequireXmt(NodesValue, Attribute.Integer("definition"), 80)
    TypesValue = Definition.Indexes("fields")
    FieldsValue = Attribute.Indexes("fields")
    if (
        not TypesValue
        or TypesValue[0] != 2
        or len(TypesValue) != len(FieldsValue)
        or any(FieldsValue[1:])
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep body has an alternate physical attribute"
        )
    DataValue = RequireXmt(NodesValue, FieldsValue[0], 83).FieldsValue["values"]
    if not isinstance(DataValue, tuple):
        raise ValueError("SOLIDWORKS saved sweep body has no typed physical values")
    Values = CastValue(tuple[object, ...], DataValue)
    if len(Values) != CountValue:
        raise ValueError(
            "SOLIDWORKS saved sweep body has an invalid physical attribute width"
        )
    return tuple(RequireScalar(Value) for Value in Values)


# every physical face identity must point back to the source sweep and its creation event
def CheckSwFaceIds(
    NodesValue: Mapping[int, XmtNode],
    FaceValues: tuple[XmtNode, ...],
    FeatureId: int,
    CreatedAt: int,
) -> None:
    for FaceValue in FaceValues:
        AttrValue = ReadBodyAttrs(NodesValue, FaceValue)["FACE_ID_2001"]
        Definition = RequireXmt(NodesValue, AttrValue.Integer("definition"), 80)
        FieldsValue = AttrValue.Indexes("fields")
        if (
            len(FieldsValue) != 4
            or Definition.Indexes("fields")[2] != 1
            or any(FieldsValue[:2])
        ):
            raise ValueError(
                "SOLIDWORKS saved sweep face has an alternate producer record"
            )
        OwnerValue = RequireXmt(NodesValue, FieldsValue[2], 82).Indexes("values")
        if len(OwnerValue) != 6 or OwnerValue[1:3] != (FeatureId, CreatedAt):
            raise ValueError("SOLIDWORKS saved sweep face has a foreign creator")
