from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep


# generated reference rows remain in the public timeline while planning consumes the solid operations
def StockReadSteps(DocumentValue: CadDocument) -> tuple[FeatureStep, ...]:
    return tuple(
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if StepValue.operation is not None
    )
