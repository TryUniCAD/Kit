from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.ThinRevolve import ThinRevolve


# any typed angular model must remain on the revolve route even when its exact scope rejects it
def HasThinWrite(DocumentValue: CadDocument) -> bool:
    return any(
        isinstance(StepValue.definition, ThinRevolve)
        for StepValue in DocumentValue.feature_timeline
    )


# the registry must apply the native measured revolve boundary before selecting or writing a destination
def PlanThinWrite(DocumentValue: CadDocument) -> RevolvePlan:
    if len(DocumentValue.feature_timeline) != 1 or not HasThinWrite(DocumentValue):
        raise ValueError("measured thin revolve requires one portable authored feature")
    CheckPlainScope(DocumentValue)
    return ProjectRevolve(DocumentValue)
