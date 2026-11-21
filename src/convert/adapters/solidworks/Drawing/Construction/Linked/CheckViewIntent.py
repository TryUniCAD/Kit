from convert.adapters.solidworks.Drawing.Construction.Projection.ViewProjection import (
    ViewProjection,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadViewMatrix import (
    ReadViewMatrix,
)
from interchange.document.Models.Drawing.DrawingView import DrawingView


# supplied portable geometric caches may be retained only when they exactly describe the independently derived canonical view
def CheckViewIntent(IntentValue: DrawingView, Projection: ViewProjection) -> None:
    Outline = tuple(
        NeedDrawNumber(Projection.FieldsValue[NameValue])
        for NameValue in ("f6d8", "f6e0", "f6e8", "f6f0")
    )
    FrameValue = NeedConceptMap(Projection.FieldsValue["f5e0"])
    MatrixValue = ReadViewMatrix(FrameValue, NeedDrawNumber(FrameValue["f70"]))
    if IntentValue.OutlineValues is not None and IntentValue.OutlineValues != Outline:
        raise ValueError(
            "portable outline conflicts with the generated child projection"
        )
    if IntentValue.ModelToSheet is not None and IntentValue.ModelToSheet != MatrixValue:
        raise ValueError(
            "portable transform conflicts with the generated canonical view"
        )
