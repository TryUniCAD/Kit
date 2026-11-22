from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckRectRules import (
    CheckRectRules,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectParams import (
    ReadRectParams,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid


# exact rectangle relation admission must precede reuse of the unchanged plain boss geometry and ownership projection
def ProjectRectDims(DocumentValue: CadDocument) -> BlindPlan:
    if type(DocumentValue) is not CadDocument:
        raise TypeError("dimensioned rectangle requires an actual neutral document")
    AssertValid(DocumentValue)
    if (
        len(DocumentValue.parameters),
        len(DocumentValue.sketches),
        len(DocumentValue.feature_timeline),
    ) != (3, 1, 1):
        raise ValueError(
            "dimensioned rectangle requires exactly three lengths one sketch and one boss"
        )
    WidthParam, HeightParam, DepthParam = ReadRectParams(DocumentValue)
    SketchValue = DocumentValue.sketches[0]
    CheckRectRules(SketchValue, (WidthParam, HeightParam))
    BareSketch = ReplaceValue(SketchValue, constraints=(), parameter_ids=())
    BareDocument = ReplaceValue(
        DocumentValue, parameters=(DepthParam,), sketches=(BareSketch,)
    )
    PlanValue = ProjectBlind(BareDocument, ReadRectSketch)
    VerticesValue = PlanValue.VerticesValue
    FirstU, FirstV = VerticesValue[0]
    LastU, LastV = VerticesValue[2]
    if (
        not FirstU < LastU
        or VerticesValue[1] != (LastU, FirstV)
        or VerticesValue[3] != (FirstU, LastV)
        or FirstV >= LastV
    ):
        raise ValueError(
            "dimensioned rectangle must follow its admitted local axis order"
        )
    for Parameter, LengthValue in (
        (WidthParam, PlanValue.WidthValue),
        (HeightParam, PlanValue.HeightValue),
    ):
        if ReadLength(Parameter.value) != LengthValue:
            raise ValueError(
                "rectangle driving parameters disagree with their authored endpoint distances"
            )
    return ReplaceValue(
        PlanValue, SketchDriverNames=(WidthParam.name, HeightParam.name)
    )
