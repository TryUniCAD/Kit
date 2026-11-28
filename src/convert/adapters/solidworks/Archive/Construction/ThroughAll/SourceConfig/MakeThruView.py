from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceConfig.MakeThruConfig import (
    MakeThruConfig,
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
from convert.adapters.solidworks.Archive.Views.MakeViewPair import MakeViewPair
from convert.adapters.solidworks.Archive.Views.ViewInput import ViewInput


# a fresh source component derives its camera from semantic inputs while preserving the previous default composer
def MakeThruView(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    IntentValue: ThruCfgIntent,
    ViewValue: ViewInput,
) -> ThruConfigGraph:
    ModelValue, PanValue = MakeViewPair(ViewValue)
    GraphValue = MakeThruConfig(InputValue, SettingsValue, IntentValue)
    FieldsValue = GraphValue.DefinitionValue.DocumentValue.FieldsValue
    FieldsValue["fae8"] = ModelValue
    FieldsValue["faf0"] = PanValue
    return GraphValue
