from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.ProjectEllipse import (
    ProjectEllipse,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument


# an ellipse shape alone cannot authorize omission of extended neutral model semantics
def PlanEllipse(DocumentValue: CadDocument) -> EllipsePlan:
    CheckPlainScope(DocumentValue)
    if not DocumentValue.capabilities <= KPartWriteCaps:
        raise ValueError("ellipse preparation has unrepresented capabilities")
    return ProjectEllipse(DocumentValue)
