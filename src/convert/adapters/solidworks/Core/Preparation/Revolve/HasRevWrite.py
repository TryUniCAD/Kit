from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# any typed angular model must remain on the revolve route even when its exact scope rejects it
def HasRevWrite(DocumentValue: CadDocument) -> bool:
    return any(
        isinstance(StepValue.definition, AngularRevolve)
        for StepValue in DocumentValue.feature_timeline
    )
