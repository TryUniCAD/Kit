from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.Revolves.ThinRevolve import ThinRevolve


# the measured thin wall scopes must bind all model owners before native staging
def PlanThinPart(DocumentValue: CadDocument) -> RevolvePlan | None:
    if not any(
        isinstance(FeatureValue.definition, ThinRevolve)
        for FeatureValue in DocumentValue.feature_timeline
    ):
        return None
    return ProjectRevolve(DocumentValue)
