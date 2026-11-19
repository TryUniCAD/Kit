from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import (
    ReadCylWords,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylRef import ReadCylRef


# both adjacent cap identities and their null positions must survive the active face selection projection
def CheckCylCaps(ChildValue: CylChild, FaceValue: Mapping[str, object]) -> None:
    RowsValue = ReadRows(FaceValue.get("f10"))
    if (
        len(RowsValue) != 5
        or RowsValue[2].get("f08") is not None
        or RowsValue[4].get("f08") is not None
    ):
        raise ValueError("concentric selected face lost its ordered cap and null rows")
    KernelCaps = tuple(
        ReadCylWords(ChildValue.NodesValue, Value)
        for Value in ChildValue.NodesValue.values()
        if Value.KindValue == 14 and Value is not ChildValue.FaceValue
    )
    if any(
        len(Value) != 6 or Value[0] != 40 or Value[3] != 0 or Value[5] != 0
        for Value in KernelCaps
    ):
        raise ValueError("concentric kernel cap profile is unqualified")
    ActiveCaps: list[tuple[int, int, int, int]] = []
    for IndexValue in (1, 3):
        CapValue = RequireNode(RowsValue[IndexValue].get("f08"), "moEndFaceSurfIdRep_c")
        FeatureId, CreationTime = ReadCylRef(CapValue, ChildValue)
        ActiveCaps.append(
            (
                FeatureId,
                CreationTime,
                FieldInt(CapValue.FieldsValue, "f38"),
                FieldInt(CapValue.FieldsValue, "f3c"),
            )
        )
    if sorted(ActiveCaps) != sorted(
        (Value[1], Value[2], Value[4], Value[5]) for Value in KernelCaps
    ):
        raise ValueError(
            "concentric adjacent cap identities differ from the actual child"
        )
