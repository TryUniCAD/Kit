from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# ordered insertion establishes two distinct endpoint handles and one use count for each actual incident line
def WireRingMut(
    SketchValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ...],
    LineValues: tuple[ArchiveNode, ...],
) -> None:
    for IndexValue, PointValue in enumerate(PointValues):
        FirstIndex = 0 if IndexValue == 0 else IndexValue - 1
        SecondIndex = len(LineValues) - 1 if IndexValue == 0 else IndexValue
        PointValue.FieldsValue["h1"] = MakeLineHandle(
            SketchValue, LineValues[FirstIndex], FirstIndex
        )
        PointValue.FieldsValue["h2"] = MakeLineHandle(
            SketchValue, LineValues[SecondIndex], SecondIndex
        )
        PointValue.FieldsValue["fe8"] = 2
