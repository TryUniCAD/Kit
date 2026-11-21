from convert.adapters.solidworks.Archive.Construction.BodyNames.FinishNamedPart import (
    FinishNamedPart,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.NameOutputMut import (
    NameOutputMut,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.PlainBodyView import (
    PlainBodyView,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyKeys import (
    ReadBodyKeys,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyLabel import (
    ReadBodyLabel,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindPart,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import (
    MakeRectDimPart,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# the portable body name must be represented by generated ownership while default bodies retain the established byte path
def MakeNamedPart(
    DocumentValue: CadDocument,
    InputValue: PartBuildInput,
    DimensionInput: RectDimInput | None = None,
) -> PartCandidate:
    NameValue = ReadBodyLabel(DocumentValue)
    BaseDocument = PlainBodyView(DocumentValue)
    CandidateValue = (
        MakeBlindPart(BaseDocument, InputValue)
        if DimensionInput is None
        else MakeRectDimPart(BaseDocument, InputValue, DimensionInput)
    )
    if NameValue == DocumentValue.feature_timeline[0].name:
        return CandidateValue
    if type(CandidateValue.PlanValue) is not BlindPlan:
        raise ValueError("named body requires the actual ordinary rectangle plan")
    if (
        CandidateValue.PlanValue.BodyId != DocumentValue.bodies[0].id
        or CandidateValue.PlanValue.FeatureId != DocumentValue.feature_timeline[0].id
    ):
        raise ValueError("named body plan differs from its actual neutral owners")
    SketchDims = ReadBodyKeys(DocumentValue, CandidateValue.PlanValue, InputValue)
    _ = NameOutputMut(CandidateValue, NameValue)
    return FinishNamedPart(CandidateValue, InputValue, SketchDims)
