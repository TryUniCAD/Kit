from dataclasses import replace as ReplaceValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import (
    MakeAnchorPart,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Materials.PlanMatPart import (
    PlanMatPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# controlled material lifecycles used the platform view arithmetic in the ordinary part recipe
def PrepMatPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    PlanValue, AnchorValue, MaterialValue = PlanMatPart(DocumentValue)
    (ConfigValue,) = DocumentValue.configurations
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested material part configuration is unavailable")
    RecipeValue = ReplaceValue(
        MakePartRecipe(PlanValue, WrittenAt), PlatformViewMath=True
    )
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    InputValue = BindPartIntent(DocumentValue, PlanValue, RecipeValue, OutputValue)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    return MakeAnchorPart(
        InputValue, PlanValue, AnchorValue, MaterialValue=MaterialValue
    )
