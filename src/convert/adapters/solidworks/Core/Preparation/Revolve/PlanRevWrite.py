from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanRevProfile import (
    PlanRevProfile,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsRevRead import (
    IsRevRead,
)
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.ReadRevInput import (
    ReadRevInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# writer selection checks only feature and name eligibility because measurement admission happens at publication
def PlanRevWrite(DocumentValue: CadDocument, NameValue: str | None) -> RevolvePlan:
    if IsRevRead(DocumentValue):
        DocumentValue = ReadRevInput(
            DocumentValue, NameValue or DocumentValue.sketches[0].name
        )
    PlanValue = PlanRevProfile(DocumentValue)
    if PlanValue is None:
        raise ValueError("SOLIDWORKS revolve requires exactly one ordinary feature")
    return PlanValue
