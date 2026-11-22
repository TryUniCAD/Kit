from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane


# linked child construction must retain every validated principal name while reusing the qualified common target recipe
def MakeChildRecipe(
    Document: CadDocument,
    PlanValue: BlindPlan,
    PlaneValues: Mapping[str, SupportPlane],
    NativeSelf: SelfFileInput,
) -> PartBuildInput:
    RecipeValue = MakePartRecipe(PlanValue, NativeSelf.SavedAt)
    RecipeValue = BindPartIntent(Document, PlanValue, RecipeValue, NativeSelf)
    SystemValue = ReplaceValue(
        RecipeValue.SystemValue,
        PlaneNames=tuple(
            (AxisValue, PlaneValues[AxisValue].name) for AxisValue in "xyz"
        ),
    )
    return ReplaceValue(RecipeValue, SystemValue=SystemValue)
