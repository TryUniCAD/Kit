from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import (
    MakeCirclePart,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from interchange.document.Models.DocumentModel import CadDocument


# circle composition must preserve the real selected configuration and final target identity through the already shared typed part composer
def RunCirclePrep(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    PlanValue: CirclePlan,
    RecipeValue: PartBuildInput,
    SettingsValue: WriteOptions,
) -> PartCandidate:
    ConfigValue = DocumentValue.configurations[0]
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested circle write configuration is unavailable")
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    InputValue = BindPartIntent(DocumentValue, PlanValue, RecipeValue, OutputValue)
    return MakeCirclePart(DocumentValue, InputValue)
