from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureKinds import ChamferFeature


# even an unsupported chamfer must reach its checked preparation guard before another native route
def IsChmfPart(DocumentValue: CadDocument) -> bool:
    return any(
        StepValue.kind == FeatureKind.KChamfer
        or isinstance(StepValue.definition, ChamferFeature)
        for StepValue in DocumentValue.feature_timeline
    )
