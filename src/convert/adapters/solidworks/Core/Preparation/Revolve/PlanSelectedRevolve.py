from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.ProjectSelectedRevolve import (
    ProjectSelectedRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.SelectedRevolvePlan import (
    SelectedRevolvePlan,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# the registry can select only the independently measured principal plane selected stock profile
def PlanSelectedRevolve(DocumentValue: CadDocument) -> SelectedRevolvePlan | None:
    Operations = DocumentValue.feature_timeline
    if len(Operations) != 3 or not all(
        isinstance(Value.definition, AngularRevolve) for Value in Operations
    ):
        return None
    Plan = ProjectSelectedRevolve(DocumentValue)
    if Plan.OperationsValue[0].AxisValue not in ("x", "y"):
        raise ValueError("public selected revolve cut requires canonical Top or Right")
    return Plan
