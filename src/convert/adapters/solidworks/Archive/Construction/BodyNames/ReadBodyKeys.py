from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# reemitting a named body must preserve the same actual rectangle driver names lengths and presentation units
def ReadBodyKeys(
    DocumentValue: CadDocument, PlanValue: BlindPlan, InputValue: PartBuildInput
) -> tuple[KeywordDim, ...]:
    if len(DocumentValue.parameters) == 1:
        return ()
    if len(DocumentValue.parameters) != 3:
        raise ValueError("named rectangle requires its exact three driving owners")
    ScaleValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}[
        InputValue.DocumentUnits.LengthUnit
    ]
    return tuple(
        KeywordDim(NameValue, LengthValue / ScaleValue, None)
        for NameValue, LengthValue in zip(
            PlanValue.SketchDriverNames,
            (PlanValue.WidthValue, PlanValue.HeightValue),
            strict=True,
        )
    )
