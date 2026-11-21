from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)


# orthogonal rectangle edits require one unary relation on each actual line without consuming a model persistent identity
def MakeAxisDim(GraphValue: PolygonGraph, IndexValue: int) -> dict[str, object]:
    FieldsValue = DimBaseFields()
    FieldsValue.update(
        {
            "_sketch": GraphValue.SketchValue,
            "f80": 4 if IndexValue % 2 == 0 else 5,
            "f90": 2,
            "f94": 0,
            "f98": 0,
            "fa0": 0xFFFE,
            "fa4": 0,
            "h1": MakeLineHandle(
                GraphValue.SketchValue, GraphValue.LineValues[IndexValue], IndexValue
            ),
        }
    )
    return FieldsValue
