from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import (
    PartRootInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakePartRefs import (
    MakePartRefs,
)
from convert.adapters.solidworks.Archive.Construction.System.MakePartSysMut import (
    MakePartSysMut,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruConfigGraph import (
    ThruConfigGraph,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.ThruCfgIntent import (
    ThruCfgIntent,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.CheckThruInput import (
    CheckThruInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.FinishThruGraph import (
    FinishThruGraph,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)


# source identity needs shared system factories while unrelated output settings remain explicit and incomplete
def MakeThruConfig(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    IntentValue: ThruCfgIntent,
) -> ThruConfigGraph:
    CheckThruInput(InputValue, SettingsValue)
    if type(IntentValue) is not ThruCfgIntent:
        raise TypeError(
            "source configuration composition requires typed semantic intent"
        )
    if (
        IntentValue.ManagerValue.ConfigValues[0].NameValue
        != InputValue.ShapeValue.StockValue.ConfigName
    ):
        raise ValueError(
            "source configuration intent differs from actual stock ownership"
        )
    IdsValue = PersistentIds()
    RefsValue = MakePartRefs(
        SettingsValue.StyleValue,
        SettingsValue.DocumentUnits,
        SettingsValue.AnalysisUnits,
    )
    SystemValue = MakePartSysMut(
        PartRootInput(IntentValue.ModelName, SettingsValue.HatchName, 19000),
        RefsValue,
        IntentValue.ManagerValue,
        SettingsValue.SystemValue,
        SettingsValue.TargetValue,
        IdsValue,
    )
    return ThruConfigGraph(
        FinishThruGraph(InputValue, SettingsValue, SystemValue, IdsValue),
        MakePartDef(IntentValue.DefinitionValue, IntentValue.DensityValue),
    )
