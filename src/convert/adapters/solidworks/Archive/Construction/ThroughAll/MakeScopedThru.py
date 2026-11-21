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
    BossValue = CandidateValue.BossValue
    EndValue = BossValue.EndValue
    Fields = EndValue.FieldsValue
    Primary, Secondary, ForwardDraft, ReverseDraft = BossValue.DimensionsValue
    if (
        ScopeGraph.FeatureValue is not BossValue.FeatureValue
        or ScopeGraph.FeatureValue.FieldsValue.get("f818") is not EndValue
        or (Fields["f08"], Fields["f0c"], Fields["f10"], Fields["f8c"]) != (1, 6, 0, 0)
        or Fields["f18"] is not Primary.DisplayValue
        or Fields["f20"] is not Secondary.DisplayValue
        or Fields["fc8"] is not ForwardDraft.DisplayValue
        or Fields["fd0"] is not ReverseDraft.DisplayValue
    ):
        raise ValueError("selected stock requires its actual forward mid plane end")
    Fields["f20"] = None
    PartValue = FinishScopePart(CandidateValue, SettingsValue)
    return ScopedPart(PartValue, ScopeGraph)
