from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import (
    PlanRevolve,
)
from interchange.document.Models.DocumentModel import CadDocument


# the disclosed end batch covers ordinary rectangles with no source annotations or equal length relation
def PlanRevEnd(DocumentValue: CadDocument) -> RevolvePlan:
    CheckPlainScope(DocumentValue)
    PlanValue = PlanRevolve(DocumentValue, AllowMeasuredMid=True)
    if PlanValue is None or PlanValue.EqualRule is not None:
        raise ValueError("measured revolve ends require one ordinary rectangular boss")
    return PlanValue
