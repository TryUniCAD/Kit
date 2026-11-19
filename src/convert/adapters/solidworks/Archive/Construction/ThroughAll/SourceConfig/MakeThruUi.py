from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruLines import (
    MakeThruLines,
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
from convert.adapters.solidworks.Archive.Definition.PartUi.MakePartUi import MakePartUi
from convert.adapters.solidworks.Archive.Definition.PartUi.PartUiInput import (
    PartUiInput,
)
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# fresh composition adds the proven scalar owners without forwarding any source environment or window record
def MakeThruUi(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    IntentValue: ThruCfgIntent,
    ViewValue: ViewInput,
    ManagerValue: EmptyMgrInput,
    LineValue: LineTableInput,
    UiValue: PartUiInput,
) -> ThruConfigGraph:
    UiFields = MakePartUi(UiValue)
    GraphValue = MakeThruLines(
        InputValue, SettingsValue, IntentValue, ViewValue, ManagerValue, LineValue
    )
    GraphValue.DefinitionValue.DocumentValue.FieldsValue.update(UiFields)
    return GraphValue
