from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# native part preparation must construct its only recipe from the neutral model target policy and one writer event before output is touched
def PrepareNative(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    OptionsValue: WriteOptions | None = None,
) -> PartCandidate:
    SettingsValue = CheckPartOpts(OptionsValue)
    PlanValue = PlanPartWrite(DocumentValue)
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    return RunPartPrep(
        DocumentValue, TargetValue, PlanValue, RecipeValue, SettingsValue
    )
