from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruView import (
    MakeThruView,
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
from convert.adapters.solidworks.Archive.Definition.EmptyManagers.MakeEmptyMgrs import (
    MakeEmptyMgrs,
)
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# fresh source composition adds only independently constructed empty owners while all unsupported source state stays refused
def MakeThruMgrs(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    IntentValue: ThruCfgIntent,
    ViewValue: ViewInput,
    ManagerValue: EmptyMgrInput,
) -> ThruConfigGraph:
    ManagerFields = MakeEmptyMgrs(ManagerValue)
    GraphValue = MakeThruView(InputValue, SettingsValue, IntentValue, ViewValue)
    GraphValue.DefinitionValue.DocumentValue.FieldsValue.update(ManagerFields)
    return GraphValue
