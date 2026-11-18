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
def MakeOriginBoxPart(
    DocumentValue: CadDocument,
    PathValue: str,
    CreationTime: int,
    TextValue: PartTextInput,
    *,
    UnitsValue: UnitInput | None = None,
) -> PartCandidate:
    OutputValue = RequirePartPath(PathValue, CreationTime)
    PlainValue = PlainBodyView(DocumentValue)
    PlanValue = ProjectRectDims(PlainValue)
    RecipeValue = MakePartRecipe(PlanValue, CreationTime)
    if UnitsValue is not None:
        RecipeValue = ReplaceValue(RecipeValue, DocumentUnits=UnitsValue)
    InputValue = ReplaceValue(
        BindPartIntent(PlainValue, PlanValue, RecipeValue, OutputValue),
        PropertiesValue=TextValue,
    )
    Margin = min(PlanValue.WidthValue, PlanValue.HeightValue) / 4
    Presentation = RectDimInput(
        (PlanValue.WidthValue / 2, -Margin),
        (PlanValue.WidthValue + Margin, PlanValue.HeightValue / 2),
        False,
        1,
        False,
    )
    return MakeAnchorNamed(
        DocumentValue, InputValue, AnchorPartInput("corner", Presentation)
    )
