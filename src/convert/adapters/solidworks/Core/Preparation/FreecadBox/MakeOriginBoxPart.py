from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorNamed import (
    MakeAnchorNamed,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.PlainBodyView import (
    PlainBodyView,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange.document.Models.DocumentModel import CadDocument


# translated origin stock must bind its source metadata to the same shared part graph and anchor that encode the dimension owners
def MakeOriginBox(
    DocumentValue: CadDocument,
    PathValue: str,
    CreationTime: int,
    TextValue: PartTextInput,
    *,
    UnitsValue: UnitInput | None = None,
    TopAttached: bool = False,
) -> PartCandidate:
    OutputValue = RequirePartPath(PathValue, CreationTime)
    PlainValue = PlainBodyView(DocumentValue)
    PlanValue = ProjectRectDims(PlainValue, TopAttached=TopAttached)
    RecipeValue = MakePartRecipe(PlanValue, CreationTime)
    if UnitsValue is not None:
        RecipeValue = ReplaceValue(RecipeValue, DocumentUnits=UnitsValue)
    InputValue = ReplaceValue(
        BindPartIntent(PlainValue, PlanValue, RecipeValue, OutputValue),
        PropertiesValue=TextValue,
    )
    Margin = min(PlanValue.WidthValue, PlanValue.HeightValue) / 4
    WidthText = (PlanValue.WidthValue / 2, Margin if TopAttached else -Margin)
    HeightText = (
        (-Margin, -PlanValue.HeightValue / 2)
        if TopAttached
        else (PlanValue.WidthValue + Margin, PlanValue.HeightValue / 2)
    )
    Presentation = RectDimInput(
        WidthText,
        HeightText,
        False,
        1,
        False,
    )
    return MakeAnchorNamed(
        DocumentValue, InputValue, AnchorPartInput("corner", Presentation, TopAttached)
    )


# the pinned attached box worker still imports the historical box constructor name
MakeOriginBoxPart = MakeOriginBox
