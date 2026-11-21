from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.Preparation.IsStockChain import IsStockChain
from convert.adapters.solidworks.Core.Preparation.TwoStock.PlanTwoStocks import (
    PlanTwoStocks,
)
from convert.adapters.solidworks.Core.Writing.IsPartTarget import IsPartTarget
from interchange.document.Models.DocumentModel import CadDocument


# the depthless evidence must come from the writer that can construct the selected cut
class StockEndWriter:
    __slots__ = ()

    # only the measured selected cut may use a depthless root owner on the actual part target
    def ProveThroughEnd(
        self, DocumentValue: CadDocument, TargetValue: KTargetType
    ) -> str | None:
        if not IsStockChain(DocumentValue):
            return None
        try:
            PlanValue = PlanTwoStocks(DocumentValue)
        except (TypeError, ValueError):
            return None
        if IsPartTarget(PlanValue.NameValue, TargetValue):
            return DocumentValue.feature_timeline[-1].id
        return None
