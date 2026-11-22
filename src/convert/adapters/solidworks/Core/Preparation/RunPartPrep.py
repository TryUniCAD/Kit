from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindPartFromPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import (
    BuildOriginBox,
)
from interchange.document.Models.DocumentModel import CadDocument


# both part preparation paths must use the actual projected model and enforce configuration and final file ownership together
def RunPartPrep(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    PlanValue: BlindPlan,
    RecipeValue: PartBuildInput,
    SettingsValue: WriteOptions,
    *,
    TopCorner: bool = False,
) -> PartCandidate:
    ConfigValue = DocumentValue.configurations[0]
    if SettingsValue.configuration not in (
        None,
        ConfigValue.id,
        ConfigValue.name,
    ):
        raise ValueError("requested write configuration is unavailable")
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    InputValue = BindPartIntent(DocumentValue, PlanValue, RecipeValue, OutputValue)
    if TopCorner:
        return BuildOriginBox(
            DocumentValue, PlanValue, InputValue, TopAttached=True
        )
    return MakeBlindPartFromPlan(DocumentValue, InputValue, PlanValue)
