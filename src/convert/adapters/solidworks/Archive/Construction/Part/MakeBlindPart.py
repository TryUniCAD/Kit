from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import (
    MakePartProfMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import (
    ProjectPlain,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from interchange.document.Models.DocumentModel import CadDocument


# the first complete donor free sdk candidate must synthesize every native stream from the actual neutral graph and explicit construction settings
def MakeBlindPart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> PartCandidate:
    return MakeBlindPartFromPlan(DocumentValue, InputValue, ProjectPlain(DocumentValue))


# an admitted closed profile must use the same graph allocation linked stream writers and container path
def MakeBlindByPlan(
    DocumentValue: CadDocument, InputValue: PartBuildInput, PlanValue: BlindPlan
) -> PartCandidate:
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(
        InputValue, PlanValue.NameValue, PlanValue.ConfigName, Allocator
    )
    ProfileValue = MakePartProfMut(SystemValue, InputValue, PlanValue, Allocator)
    return FinishBlindMut(SystemValue, ProfileValue, InputValue, PlanValue, Allocator)


# existing rectangle and polygon callers need the established plan entry while its implementation follows the declaration naming limit
MakeBlindPartFromPlan = MakeBlindByPlan
