from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindByPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import (
    MakePartProfMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Shells.OpenShellPlan import (
    OpenShellPlan,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeAxisOnlyMut import (
    MakeAxisOnlyMut,
)
from interchange.document.Models.DocumentModel import CadDocument


# both shell stock forms use the ordinary blind boss and the constrained form publishes its four authored axes
def MakeShellStock(
    DocumentValue: CadDocument, PlanValue: OpenShellPlan, Settings: PartBuildInput
) -> PartCandidate:
    StockValue = PlanValue.StockValue
    if not PlanValue.HasAxisRules:
        return MakeBlindByPlan(DocumentValue, Settings, StockValue)
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(Settings, StockValue, Allocator)
    ProfileValue = MakePartProfMut(SystemValue, Settings, StockValue, Allocator)
    MakeAxisOnlyMut(ProfileValue, Allocator)
    return FinishBlindMut(SystemValue, ProfileValue, Settings, StockValue, Allocator)
