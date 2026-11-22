from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.SweepFeature import SweepFeature


# typed sweep intent must reach its own checks before another profile can reinterpret it
def IsSweepPart(DocumentValue: CadDocument) -> bool:
    return any(
        isinstance(StepValue.definition, SweepFeature)
        for StepValue in DocumentValue.feature_timeline
    )
