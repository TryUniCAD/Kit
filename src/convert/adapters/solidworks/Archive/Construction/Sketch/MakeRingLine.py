from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# ordered ring lines need actual endpoints and separate creation permanent and endpoint index namespaces
def MakeRingLine(
    SketchValue: ArchiveNode, PointValues: tuple[ArchiveNode, ...], IndexValue: int
) -> ArchiveNode:
    EndIndex = (IndexValue + 1) % len(PointValues)
    FieldsValue = EntityFields(SketchValue)
    FieldsValue.update(
        {
            "_start": PointValues[IndexValue],
            "_end": PointValues[EndIndex],
            "f08": IndexValue + 1,
            "f0c": IndexValue + 1,
            "fd0": 1,
            "fd4": 0,
            "seg_tol": -1.0,
            "fe8": 0,
            "fc8_s": min(IndexValue, 0xFFFF),
            "fc8": IndexValue,
            "fcc_s": min(EndIndex, 0xFFFF),
            "fcc": EndIndex,
        }
    )
    return ArchiveNode(RuntimeClass("sgLine", 1), FieldsValue)
