from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockModel import (
    KLegacyStop,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ProjectTyped import ProjectTyped


# the old unsupported diagnostic can be cleared only after typed projection succeeds
def BindStockModel(
    Model: NativeModel,
    LinkValue: NativeLink,
    OwnersValue: StockCutLineage | ColdStockOwners,
) -> NativeModel:
    Bound = ProjectTyped(Model, LinkValue, StockValue=OwnersValue)
    return ReplaceValue(
        Bound,
        diagnostics=tuple(
            Message
            for Message in Bound.diagnostics
            if Message != f"typed resolved semantics unavailable: {KLegacyStop}"
        ),
    )
