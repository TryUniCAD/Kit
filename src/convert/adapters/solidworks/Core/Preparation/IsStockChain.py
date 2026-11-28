from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind


# only the two producer sequence needs the dedicated selected stock planner
def IsStockChain(DocumentValue: CadDocument) -> bool:
    return tuple(
        (StepValue.kind, StepValue.operation)
        for StepValue in DocumentValue.feature_timeline
    ) == (
        (FeatureKind.KExtrusion, BooleanOp.KCreate),
        (FeatureKind.KExtrusion, BooleanOp.KCreate),
        (FeatureKind.KExtrusion, BooleanOp.KCutOperation),
    )
