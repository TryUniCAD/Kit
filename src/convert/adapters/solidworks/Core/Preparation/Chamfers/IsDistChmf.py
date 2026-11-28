from interchange.Features.FeatureKinds import ChamferFeature
from interchange.document.Models.DocumentModel import CadDocument


# the two linear chamfer modes require their own exact measurement boundary
def IsDistChmf(DocumentValue: CadDocument) -> bool:
    return any(
        isinstance(StepValue.definition, ChamferFeature)
        and StepValue.definition.mode in ("equal_distance", "two_distances")
        for StepValue in DocumentValue.feature_timeline
    )
