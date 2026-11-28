from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.FinishNamedPart import (
    FinishNamedPart,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorBase import (
    MakeAnchorBase,
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
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from interchange.document.Models.DocumentModel import CadDocument


# authored body labels must attach to the generated anchored output without replacing its real contour dimension or origin owners
def MakeAnchorNamed(
    DocumentValue: CadDocument,
    InputValue: PartBuildInput,
    AnchorValue: AnchorPartInput,
) -> PartCandidate:
    NameValue = ReadBodyLabel(DocumentValue)
    CandidateValue = MakeAnchorBase(
        PlainBodyView(DocumentValue), InputValue, AnchorValue
    )
    if NameValue == DocumentValue.feature_timeline[0].name:
        return CandidateValue
    PlanValue = CandidateValue.PlanValue
    if type(PlanValue) is not BlindPlan:
        raise ValueError("anchored body requires its actual rectangular boss plan")
    if (
        PlanValue.BodyId != DocumentValue.bodies[0].id
        or PlanValue.FeatureId != DocumentValue.feature_timeline[0].id
    ):
        raise ValueError("anchored body plan differs from its actual neutral owners")
    SketchDims = ReadBodyKeys(DocumentValue, PlanValue, InputValue)
    _ = NameOutputMut(CandidateValue, NameValue)
    return FinishNamedPart(CandidateValue, InputValue, SketchDims)
