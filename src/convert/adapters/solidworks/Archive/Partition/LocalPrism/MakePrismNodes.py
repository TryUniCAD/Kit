from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismNullFields import (
    KPrismNullFields,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalLimit,
    KLocalShapes,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.Geometry.Parasolid import KMissingParam


# the schema needs all proven fields and independent transmit and persistent entity indices
def BindPrismFields(
    CellValue: PrismCell,
    Indices: Mapping[PrismRef, int],
    PersistentValue: int,
    LastEntity: int,
) -> XmtNode:
    RefValue = CellValue.RefValue
    KindValue = RefValue.KindValue
    FieldsValue: dict[str, object] = dict.fromkeys(KPrismNullFields[KindValue], 0)
    FieldsValue.update(
        {
            NameValue: Indices[Value] if isinstance(Value, PrismRef) else Value
            for NameValue, Value in CellValue.FieldsValue.items()
        }
    )
    if RefValue == KPrismBody:
        FieldsValue["highest_node_id"] = LastEntity
    elif KindValue != 17:
        FieldsValue["node_id"] = PersistentValue
    if KindValue in (14, 16, 18):
        FieldsValue["tolerance"] = KMissingParam
    ShapeValue = KLocalShapes[KindValue]
    if FieldsValue.keys() != {
        FieldValue.NameValue for FieldValue in ShapeValue.FieldsValue
    }:
        raise ValueError(f"local prism has unclassified {ShapeValue.NameValue} fields")
    return XmtNode(Indices[RefValue], KindValue, FieldsValue)


# resident order allocates the actual structural cells before binding any pointers
def MakePrismNodes(CellsValue: tuple[PrismCell, ...]) -> tuple[XmtNode, ...]:
    Indices = {
        CellValue.RefValue: IndexValue
        for IndexValue, CellValue in enumerate(CellsValue, 1)
    }
    if (
        len(Indices) != len(CellsValue)
        or not 0 < len(Indices) <= KLocalLimit
        or Indices.get(KPrismBody) != 1
    ):
        raise ValueError(
            "local prism requires one root and bounded distinct transmit identities"
        )
    LastEntity = sum(
        CellValue.RefValue.KindValue not in (12, 17) for CellValue in CellsValue
    )
    PersistentValue = 0
    ResultValues = []
    for CellValue in CellsValue:
        PersistentValue += int(CellValue.RefValue.KindValue not in (12, 17))
        ResultValues.append(
            BindPrismFields(CellValue, Indices, PersistentValue, LastEntity)
        )
    return tuple(ResultValues)
