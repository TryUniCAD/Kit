from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureStep import FeatureStep


# only the two producer sequence needs the dedicated selected stock planner
def IsStockChain(DocumentValue: CadDocument) -> bool:
    return IsStockOps(DocumentValue.feature_timeline)


# the same operation order must hold for authored inputs and linked native readback
def IsStockOps(StepsValue: tuple[FeatureStep, ...]) -> bool:
    return tuple((StepValue.kind, StepValue.operation) for StepValue in StepsValue) == (
        (FeatureKind.KExtrusion, BooleanOp.KCreate),
        (FeatureKind.KExtrusion, BooleanOp.KCreate),
        (FeatureKind.KExtrusion, BooleanOp.KCutOperation),
    )
