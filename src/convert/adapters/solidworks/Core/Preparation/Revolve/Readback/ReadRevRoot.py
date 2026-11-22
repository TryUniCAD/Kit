from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ThinRevolve import ThinRevolve


# the regenerated boss must use the exact public driver and consumed sketch step
def ReadRevRoot(DocumentValue: CadDocument, *, IsThin: bool = False) -> FeatureStep:
    SketchValue, Driver, BodyValue = (
        DocumentValue.sketches[0],
        DocumentValue.parameters[0],
        DocumentValue.bodies[0],
    )
    Matches = tuple(
        StepValue
        for StepValue in DocumentValue.feature_timeline
        if isinstance(StepValue.definition, ThinRevolve if IsThin else AngularRevolve)
    )
    if (
        len(Matches) != 1
        or Matches[0].id != Driver.owner_id
        or (
            IsThin
            and any(
                Value.owner_id != Matches[0].id for Value in DocumentValue.parameters
            )
        )
        or Matches[0].id != BodyValue.final_feature_id
        or Matches[0].sketch_id != SketchValue.id
        or len(Matches[0].input_feature_ids) != 1
        or not any(
            StepValue.id == Matches[0].input_feature_ids[0]
            and StepValue.sketch_id == SketchValue.id
            for StepValue in DocumentValue.feature_timeline
        )
    ):
        raise ValueError("SOLIDWORKS revolve readback lacks the actual feature owners")
    return Matches[0]
