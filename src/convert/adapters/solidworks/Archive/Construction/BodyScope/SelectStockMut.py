from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.CheckScopeFresh import (
    CheckScopeFresh,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.CheckScopeOwner import (
    CheckScopeOwner,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import (
    MakeBodyRef,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import (
    SelectedStock,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.StockBodyGraph import (
    StockBodyGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)


# selected stock attachment must preserve actual owners while keeping prior body scope and cut caches unavailable
def SelectStockMut(
    CandidateValue: PartCandidate, ScopeValue: SelectedStock
) -> StockBodyGraph:
    if type(ScopeValue) is not SelectedStock:
        raise TypeError("selected stock attachment requires explicit typed scope")
    StockValue = ScopeValue.StockValues[0]
    CutValue = CheckScopeOwner(CandidateValue, StockValue)
    ManagerValue = CheckScopeFresh(CandidateValue)
    RootValue = CandidateValue.SystemValue.RootValue
    BossValue = CandidateValue.BossValue.FeatureValue
    AtomValue = BindStockMut(ManagerValue, BossValue)
    WrapperValue = MakeBodyRef(RootValue, BossValue, AtomValue)
    BodyValues = [{"o": WrapperValue}]
    BossValue.FieldsValue["f544"] = 1
    CutValue.FeatureValue.FieldsValue.update(
        f544=1, has_f548=1, f548={"n": len(BodyValues), "items": BodyValues}
    )
    return StockBodyGraph(
        StockValue, RootValue, BossValue, AtomValue, WrapperValue, CutValue.FeatureValue
    )
