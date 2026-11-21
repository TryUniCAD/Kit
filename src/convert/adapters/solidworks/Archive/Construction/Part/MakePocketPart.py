from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindByPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPocket import (
    ProjectPocket,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from interchange.document.Models.DocumentModel import CadDocument


# an ordinary pocket adds one circular cut to the shared complete part construction
def MakePocketPart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> PartCandidate:
    PlanValue = ProjectPocket(DocumentValue)
    return MakeBlindByPlan(DocumentValue, InputValue, PlanValue.BossValue, PlanValue)
