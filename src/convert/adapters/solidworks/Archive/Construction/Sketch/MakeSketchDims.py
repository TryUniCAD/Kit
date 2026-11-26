from convert.adapters.solidworks.Archive.Construction.Sketch.DimensionArrays import (
    KDimensionArrays,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.EmptySketchRows import (
    EmptySketchRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# dimension absence must retain the complete native manager and its independently owned auxiliary list
def MakeSketchDims() -> dict[str, object]:
    FieldsValue = EmptySketchRows(KDimensionArrays)
    FieldsValue["f118"] = ArchiveNode(
        RuntimeClass("suObList", 1), EmptySketchRows((("n", "items"),))
    )
    return FieldsValue
