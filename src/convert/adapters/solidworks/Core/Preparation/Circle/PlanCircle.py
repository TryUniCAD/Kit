from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import (
    ProjectCircle,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.Circle.CheckCircMode import (
    CheckCircMode,
)
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument


# a geometric circle alone cannot establish complete admission of the authored document and its actual ownership graph
def PlanCircle(DocumentValue: CadDocument) -> CirclePlan:
    CheckPlainScope(DocumentValue)
    if not DocumentValue.capabilities <= KPartWriteCaps:
        raise ValueError("circle preparation has unrepresented capabilities")
    PlanValue = ProjectCircle(DocumentValue)
    CheckCircMode(PlanValue)
    return PlanValue
