from dataclasses import replace as ReplaceValue
from math import isclose as IsClose

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
    PlanValue = ProjectBlind(BareDocument, ReadRectSketch, DepthParam.name)
    VerticesValue = PlanValue.VerticesValue
    LeftValue, BottomValue = VerticesValue[0]
    RightValue, TopValue = VerticesValue[2]
    if (
        not LeftValue < RightValue
        or not BottomValue < TopValue
        or VerticesValue[1] != (RightValue, BottomValue)
        or VerticesValue[3] != (LeftValue, TopValue)
    ):
        raise ValueError(
            "dimensioned rectangle must start at its lower left and run counterclockwise along positive axes"
        )
    for Parameter, LengthValue in (
        (WidthParam, PlanValue.WidthValue),
        (HeightParam, PlanValue.HeightValue),
    ):
        if not IsClose(
            ReadLength(Parameter.value), LengthValue, rel_tol=1e-12, abs_tol=1e-14
        ):
            raise ValueError(
                "rectangle driving parameters disagree with their authored endpoint distances"
            )
    return ReplaceValue(
        PlanValue, SketchDriverNames=(WidthParam.name, HeightParam.name)
    )
