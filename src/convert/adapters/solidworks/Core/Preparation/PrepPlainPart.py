from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import (
    PrepareCircle,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanTopCorner import (
    PlanTopCorner,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# ordinary blind and circle preparation uses the same final target and explicit creation event
def PrepPlainPart(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    SettingsValue: WriteOptions,
) -> PartCandidate:
    TopValue = PlanTopCorner(DocumentValue)
    if TopValue is not None:
        Projected, TopPlan = TopValue
        return RunPartPrep(
            Projected,
            TargetValue,
            TopPlan,
            MakePartRecipe(TopPlan, WrittenAt),
            SettingsValue,
            TopCorner=True,
        )
    try:
        PlanValue = PlanPartWrite(DocumentValue)
    except (TypeError, ValueError):
        return PrepareCircle(DocumentValue, TargetValue, WrittenAt, SettingsValue)
    RecipeValue = MakePartRecipe(PlanValue, WrittenAt)
    return RunPartPrep(
        DocumentValue, TargetValue, PlanValue, RecipeValue, SettingsValue
    )
