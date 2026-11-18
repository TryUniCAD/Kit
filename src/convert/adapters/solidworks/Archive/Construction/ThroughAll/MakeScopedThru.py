from convert.adapters.solidworks.Archive.Construction.BodyScope.FinishScopePart import (
    FinishScopePart,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.RequireStock import (
    RequireStock,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.ScopedPart import (
    ScopedPart,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import (
    SelectedStock,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectStockMut import (
    SelectStockMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThroughPart import (
    MakeThroughPart,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)


# selected stock construction must reuse the established part path without changing its existing all bodies behavior
def MakeScopedThru(
    InputValue: ThroughPartSpec,
    SettingsValue: PartBuildInput,
    ScopeValue: SelectedStock,
) -> ScopedPart:
    RequireStock(InputValue, ScopeValue)
    CandidateValue = MakeThroughPart(InputValue, SettingsValue)
    ScopeGraph = SelectStockMut(CandidateValue, ScopeValue)
    PartValue = FinishScopePart(CandidateValue, SettingsValue)
    return ScopedPart(PartValue, ScopeGraph)
