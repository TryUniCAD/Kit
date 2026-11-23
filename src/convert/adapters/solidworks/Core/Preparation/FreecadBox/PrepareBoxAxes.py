from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.BodyNames.NameOutputMut import (
    NameOutputMut,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.PlainBodyView import (
    PlainBodyView,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyKeys import (
    ReadBodyKeys,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyLabel import (
    ReadBodyLabel,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.CheckAxisInput import (
    CheckAxisInput,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.FinishAxesPart import (
    FinishAxesPart,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxes import (
    PrincipalAxes,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import (
    MakeAnchorPart,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.FreecadBox.BoxAnchorInput import (
    BoxAnchorInput,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.CheckAxisStock import (
    CheckAxisStock,
)
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange.document.Models.DocumentModel import CadDocument


# the prepared candidate carries only editable stock and axis intent into fresh linked archives
def PrepareBoxAxes(
    DocumentValue: CadDocument,
    PathValue: str,
    CreationTime: int,
    TextValue: PartTextInput,
    AxesValue: PrincipalAxes,
    *,
    TopAttached: bool = True,
    UnitsValue: UnitInput | None = None,
) -> PartCandidate:
    NameValue = ReadBodyLabel(DocumentValue)
    Plain = PlainBodyView(DocumentValue)
    PlanValue = ProjectRectDims(Plain, TopAttached=TopAttached)
    CheckAxisStock(DocumentValue, PlanValue)
    Locator = RequirePartPath(PathValue, CreationTime)
    Recipe = MakePartRecipe(PlanValue, CreationTime)
    if UnitsValue is not None:
        Recipe = ReplaceValue(Recipe, DocumentUnits=UnitsValue)
    Settings = ReplaceValue(
        BindPartIntent(Plain, PlanValue, Recipe, Locator), PropertiesValue=TextValue
    )
    CheckAxisInput(AxesValue, Settings)
    CheckPartInput(
        Plain,
        Settings,
        PlanValue,
        tuple(Value.NameValue for Value in AxesValue.AxisValues),
    )
    Allocator = PersistentIds()
    StockValue = MakeAnchorPart(
        Settings,
        PlanValue,
        BoxAnchorInput(PlanValue, TopAttached),
        AllocatorValue=Allocator,
    )
    _ = NameOutputMut(StockValue, NameValue)
    return FinishAxesPart(
        StockValue,
        Settings,
        Allocator,
        AxesValue,
        ReadBodyKeys(DocumentValue, PlanValue, Settings),
    )
