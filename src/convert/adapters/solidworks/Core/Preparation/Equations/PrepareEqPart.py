from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.Equations.MakeDerivedBoss import (
    MakeDerivedBoss,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Equations.PlanEqPart import PlanEqPart
from convert.adapters.solidworks.Core.Preparation.FinalPartPath import FinalPartPath
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# a neutral equation part needs the ordinary part recipe and its actual fixed corner before native generation
def PrepareEqPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    Projected, PlanValue = PlanEqPart(DocumentValue)
    ConfigValue = DocumentValue.configurations[0]
    if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
        raise ValueError("requested write configuration is unavailable")
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    OutputValue = FinalPartPath(
        TargetValue, SettingsValue, RecipeValue.OutputValue, PlanValue.NameValue
    )
    InputValue = BindPartIntent(Projected, PlanValue, RecipeValue, OutputValue)
    Margin = min(PlanValue.WidthValue, PlanValue.HeightValue) / 4.0
    Placement = RectDimInput(
        (PlanValue.WidthValue / 2.0, -Margin),
        (PlanValue.WidthValue + Margin, PlanValue.HeightValue / 2.0),
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
        False,
    )
    return MakeDerivedBoss(Projected, InputValue, Placement)
