from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
)
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.Preparation.Equations.PlanEqPart import PlanEqPart
from convert.adapters.solidworks.Core.Preparation.IsStockChain import IsStockChain
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.TwoStock.PlanTwoStocks import (
    PlanTwoStocks,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import (
    TwoStockPlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# registry selection must identify the actual native part profile before any destination is staged
def PlanNativePart(DocumentValue: CadDocument) -> KPartPlan | TwoStockPlan:
    if any(Parameter.expression is not None for Parameter in DocumentValue.parameters):
        return PlanEqPart(DocumentValue)[1]
    if IsStockChain(DocumentValue):
        return PlanTwoStocks(DocumentValue)
    try:
        return PlanPartWrite(DocumentValue)
    except (TypeError, ValueError):
        return PlanCircle(DocumentValue)
