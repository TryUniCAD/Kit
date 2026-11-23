from dataclasses import replace as ReplaceValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanTopCorner import (
    PlanTopCorner,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RunPartPrep import RunPartPrep
from interchange.document.Models.DocumentModel import CadDocument


# anchored top preparation keeps the measured camera arithmetic separate from the default recipe
def PrepTopPart(
    Document: CadDocument,
    TargetValue: KTargetType,
    WrittenAt: int,
    Settings: WriteOptions,
    *,
    PlatformMath: bool = False,
) -> PartCandidate:
    TopValue = PlanTopCorner(Document)
    if TopValue is None:
        raise ValueError("SOLIDWORKS requires the actual anchored Top profile")
    Projected, PlanValue = TopValue
    Recipe = ReplaceValue(
        MakePartRecipe(PlanValue, WrittenAt), PlatformViewMath=PlatformMath
    )
    return RunPartPrep(
        Projected, TargetValue, PlanValue, Recipe, Settings, TopCorner=True
    )
