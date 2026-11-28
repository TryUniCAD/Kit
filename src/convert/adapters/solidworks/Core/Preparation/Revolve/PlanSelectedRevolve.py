from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.ProjectSelectedRevolve import (
    ProjectSelRev,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.SelectedRevolvePlan import (
    SelectedRevPlan,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# the registry can select only the independently measured principal plane selected stock profile
def PlanSelRevolve(DocumentValue: CadDocument) -> SelectedRevPlan | None:
    Operations = DocumentValue.feature_timeline
    if len(Operations) != 3 or not all(
        isinstance(Value.definition, AngularRevolve) for Value in Operations
    ):
        return None
    PlanValue = ProjectSelRev(DocumentValue)
    if PlanValue.OperationsValue[0].AxisValue not in ("x", "y"):
        raise ValueError("public selected revolve cut requires canonical Top or Right")
    return PlanValue
