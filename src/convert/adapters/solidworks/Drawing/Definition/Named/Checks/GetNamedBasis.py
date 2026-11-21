from convert.adapters.solidworks.Archive.Construction.Views.MakeStdViews import (
    MakeStdViews,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedDrawNumber,
)


# canonical orientation checks must use source derived view construction instead of captured rotation rows
def GetNamedBasis(OrientationValue: str) -> tuple[float, ...]:
    ViewsValue = MakeStdViews(1)
    ViewValue = next(
        NodeValue
        for NodeValue in ViewsValue
        if NodeValue.FieldsValue["f358"] == OrientationValue
    )
    FrameValue = NeedConceptMap(ViewValue.FieldsValue["f368"])
    if FrameValue["has_matrix"] == 0:
        return (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    MatrixValue = NeedConceptMap(FrameValue["f08"])
    return tuple(NeedDrawNumber(MatrixValue[f"m{Index}"]) for Index in range(9))
