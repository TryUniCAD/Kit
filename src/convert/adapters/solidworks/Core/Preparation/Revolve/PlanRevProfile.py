from math import tau as FullTurn

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.document.Models.DocumentModel import CadDocument


# the registry must apply the native measured revolve boundary before selecting or writing a destination
def PlanRevProfile(DocumentValue: CadDocument) -> RevolvePlan | None:
    if len(DocumentValue.feature_timeline) != 1 or not isinstance(
        DocumentValue.feature_timeline[0].definition, AngularRevolve
    ):
        return None
    CheckPlainScope(DocumentValue)
    PlanValue = ProjectRevolve(DocumentValue)
    if PlanValue.AxisValue not in ("x", "y") or PlanValue.AngleValue == FullTurn:
        raise ValueError(
            "public native revolve requires a partial boss on canonical Top or Right"
        )
    return PlanValue
