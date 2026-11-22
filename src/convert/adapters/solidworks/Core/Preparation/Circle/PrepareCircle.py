from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.Preparation.Circle.RunCirclePrep import (
    RunCirclePrep,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument


# neutral circle preparation must derive every setting from the document target policy and one explicit writer event without runtime files
def PrepareCircle(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
    *,
    Measured: bool = False,
) -> PartCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    PlanValue = PlanCircle(DocumentValue, Measured=Measured)
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    return RunCirclePrep(
        DocumentValue, TargetValue, PlanValue, RecipeValue, SettingsValue
    )
