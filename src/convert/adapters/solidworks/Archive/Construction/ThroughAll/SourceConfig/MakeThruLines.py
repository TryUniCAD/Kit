from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruMgrs import (
    MakeThruMgrs,
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
from convert.adapters.solidworks.Archive.Definition.LineTables.MakeLineTables import (
    MakeLineTables,
)
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# fresh source composition adds only line owners derived from typed patterns and native constructor insertion order
def MakeThruLines(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    IntentValue: ThruCfgIntent,
    ViewValue: ViewInput,
    ManagerValue: EmptyMgrInput,
    LineValue: LineTableInput,
) -> ThruConfigGraph:
    LineFields = MakeLineTables(LineValue)
    GraphValue = MakeThruMgrs(
        InputValue, SettingsValue, IntentValue, ViewValue, ManagerValue
    )
    GraphValue.DefinitionValue.DocumentValue.FieldsValue.update(LineFields)
    return GraphValue
