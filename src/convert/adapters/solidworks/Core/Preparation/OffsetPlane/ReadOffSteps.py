from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import RefPlaneFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch


# the inferred publication route needs the actual linked datum sketch and sole creator
def ReadOffSteps(
    DocumentValue: CadDocument, SketchValue: Sketch
) -> tuple[FeatureStep, FeatureStep, FeatureStep]:
    (Datum,) = (
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if type(StepValue.definition) is RefPlaneFeature
    )
    (Profile,) = (
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if StepValue.kind == FeatureKind.KReference
        and StepValue.sketch_id == SketchValue.id
    )
    (BossStep,) = (
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if type(StepValue.definition) is ExtrudeFeature
    )
    if (
        Profile.input_feature_ids != (Datum.id,)
        or Profile.parameter_ids != SketchValue.parameter_ids
        or BossStep.input_feature_ids != (Profile.id,)
        or BossStep.sketch_id != SketchValue.id
        or BossStep.operation != BooleanOp.KJoin
        or DocumentValue.bodies[0].final_feature_id != BossStep.id
        or not Datum.order < Profile.order < BossStep.order
    ):
        raise ValueError("SOLIDWORKS offset readback lacks its ordered feature owners")
    return Datum, Profile, BossStep
