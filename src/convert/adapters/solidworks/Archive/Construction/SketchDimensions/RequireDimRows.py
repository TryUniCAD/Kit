from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Sketch.DimensionArrays import (
    KDimensionArrays,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# appending the first rectangle drivers must not overwrite another dimension collection or an existing display owner
def RequireDimRows(SketchValue: ArchiveNode) -> MutableMapping[str, object]:
    FieldsValue = SketchValue.FieldsValue.get("dims")
    if not isinstance(FieldsValue, MutableMapping):
        raise ValueError(
            "rectangle dimensions require an owned mutable sketch dimension manager"
        )
    FieldsValue = CastValue(MutableMapping[str, object], FieldsValue)
    for CountName, FieldName in KDimensionArrays:
        if FieldInt(FieldsValue, CountName) != 0 or ReadRows(
            FieldsValue.get(FieldName)
        ):
            raise ValueError(
                "rectangle dimensions require every dimension collection to be fresh"
            )
    DisplayList = ArchiveNode.RequireNode(FieldsValue.get("f118"))
    if (
        DisplayList.ClassValue != RuntimeClass("suObList", 1)
        or FieldInt(DisplayList.FieldsValue, "n") != 0
        or ReadRows(DisplayList.FieldsValue.get("items"))
    ):
        raise ValueError(
            "rectangle dimensions require an empty actual sketch display list"
        )
    return FieldsValue
