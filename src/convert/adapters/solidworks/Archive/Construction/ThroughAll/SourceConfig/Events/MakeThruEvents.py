from convert.adapters.solidworks.Archive.Construction.Configuration.Events.ApplyCmgrMut import (
    ApplyCmgrMut,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.Events.CmgrEvents import (
    CmgrEvents,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruUi import (
    MakeThruUi,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import (
    ThruCfgIntent,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruConfigGraph import (
    ThruConfigGraph,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.EmptyMgrInput import (
    EmptyMgrInput,
)
from convert.adapters.solidworks.Archive.Definition.LineTables.LineTableInput import (
    LineTableInput,
)
from convert.adapters.solidworks.Archive.Definition.PartUi.PartUiInput import (
    PartUiInput,
)
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# source owned manager moments are composed only into fresh nodes without transferring windows or configuration caches
def MakeThruEvents(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    IntentValue: ThruCfgIntent,
    ViewValue: ViewInput,
    ManagerValue: EmptyMgrInput,
    LineValue: LineTableInput,
    UiValue: PartUiInput,
    EventValue: CmgrEvents,
) -> ThruConfigGraph:
    GraphValue = MakeThruUi(
        InputValue,
        SettingsValue,
        IntentValue,
        ViewValue,
        ManagerValue,
        LineValue,
        UiValue,
    )
    ApplyCmgrMut(
        GraphValue.OwnersValue.SystemValue, EventValue, SettingsValue.TargetValue
    )
    return GraphValue
