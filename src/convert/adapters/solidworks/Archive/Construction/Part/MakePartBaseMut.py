from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import (
    ManagerInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import (
    PartRootInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartLabels import PartLabels
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakePartRefs import (
    MakePartRefs,
)
from convert.adapters.solidworks.Archive.Construction.System.MakePartSysMut import (
    MakePartSysMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)


# the full part must reuse the proven system graph with the neutral configuration name and one shared actual allocator
def MakePartBaseMut(
    InputValue: PartBuildInput, PlanValue: PartLabels, Allocator: PersistentIds
) -> PartSystem:
    RefsValue = MakePartRefs(
        InputValue.StyleValue, InputValue.DocumentUnits, InputValue.AnalysisUnits
    )
    ConfigValue = ConfigSpec(
        PlanValue.ConfigName, "", InputValue.HeaderValue.ModifiedAt
    )
    ManagerValue = ManagerInput(InputValue.ManagerName, (ConfigValue,), 0)
    return MakePartSysMut(
        PartRootInput(PlanValue.NameValue, InputValue.HatchName, 19000),
        RefsValue,
        ManagerValue,
        InputValue.SystemValue,
        InputValue.TargetValue,
        Allocator,
    )
