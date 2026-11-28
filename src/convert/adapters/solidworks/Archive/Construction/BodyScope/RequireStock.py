from convert.adapters.solidworks.Archive.Construction.BodyScope.SelectedStock import (
    SelectedStock,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)


# an equal looking stock from another model cannot establish the actual selected body ownership
def RequireStock(
    InputValue: ThroughPartSpec, ScopeValue: SelectedStock
) -> ThroughStock:
    if type(InputValue) is not ThroughPartSpec or type(ScopeValue) is not SelectedStock:
        raise TypeError(
            "selected stock construction requires actual typed part and scope inputs"
        )
    if ScopeValue.StockValues[0] is not InputValue.StockValue:
        raise ValueError(
            "selected stock does not belong to the actual through all part input"
        )
    return InputValue.StockValue
