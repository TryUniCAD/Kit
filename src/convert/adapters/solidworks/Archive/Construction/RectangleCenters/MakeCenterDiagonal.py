from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# each construction diagonal must derive its endpoint slots and new creation identity without changing contour permanence
def MakeDiagonal(
    SketchValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ...],
    FirstValue: ArchiveNode,
    SecondValue: ArchiveNode,
    IndexValue: int,
) -> ArchiveNode:
    if FirstValue is SecondValue or any(
        Value.FieldsValue.get("_sketch") is not SketchValue
        for Value in (FirstValue, SecondValue)
    ):
        raise ValueError("center diagonal requires distinct actual local endpoints")
    FirstIndex, SecondIndex = PointValues.index(FirstValue), PointValues.index(
        SecondValue
    )
    FieldsValue = EntityFields(SketchValue)
    FieldsValue.update(
        {
            "_start": FirstValue,
            "_end": SecondValue,
            "f0c": IndexValue + 1,
            "f54": FieldInt(FieldsValue, "f54") | 8,
            "fd0": 0,
            "fd4": 0,
            "seg_tol": -1.0,
            "fe8": 0,
            "fc8_s": min(FirstIndex, 0xFFFF),
            "fc8": FirstIndex,
            "fcc_s": min(SecondIndex, 0xFFFF),
            "fcc": SecondIndex,
        }
    )
    return ArchiveNode(RuntimeClass("sgLine", 1), FieldsValue)
