from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatMap import ReadPatMap
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import LinearPattern, NativeFeature
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep


# the stock dependency must pass through its own physical sketch step
def ReadStockLink(
    StepValue: FeatureStep,
    Nodes: dict[str, FeatureStep],
    ParentIds: tuple[str, ...],
) -> None:
    if (
        StepValue.operation != BooleanOp.KJoin
        or StepValue.sketch_id is None
        or StepValue.selection_ids
        or StepValue.input_feature_ids[:-1] != ParentIds
        or not StepValue.input_feature_ids
    ):
        raise ValueError("SOLIDWORKS cold pattern lacks its original stock dependency")
    Carrier = Nodes[StepValue.input_feature_ids[-1]]
    if (
        type(Carrier.definition) is not NativeFeature
        or Carrier.sketch_id != StepValue.sketch_id
    ):
        raise ValueError("SOLIDWORKS cold pattern stock has a foreign sketch step")


# the two stocks with hinge and datum must retain their actual pattern relationships
def ReadPatHist(
    DocumentValue: CadDocument,
) -> tuple[FeatureStep, FeatureStep, FeatureStep, FeatureStep, FeatureStep]:
    Timeline = DocumentValue.feature_timeline
    Nodes = ReadPatMap(Timeline)
    Plate, SeedValue, Hinge, Angle, Pattern = (
        StepValue
        for StepValue in Timeline
        if type(StepValue.definition) is not NativeFeature
    )
    if (
        type(Plate.definition) is not ExtrudeFeature
        or type(SeedValue.definition) is not ExtrudeFeature
        or type(Hinge.definition) is not PlaneAxis
        or type(Angle.definition) is not BoundDatum
        or type(Pattern.definition) is not LinearPattern
        or Pattern.input_feature_ids != (SeedValue.id, Angle.id)
        or len(Angle.input_feature_ids) != 2
        or Angle.input_feature_ids[1] != Hinge.id
        or not all(
            len(StepValue.selection_ids) == Count
            for StepValue, Count in ((Hinge, 2), (Angle, 2), (Pattern, 1))
        )
    ):
        raise ValueError("SOLIDWORKS cold pattern has a different typed feature graph")
    ReadStockLink(Plate, Nodes, ())
    ReadStockLink(SeedValue, Nodes, (Plate.id,))
    return Plate, SeedValue, Hinge, Angle, Pattern
