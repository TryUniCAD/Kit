from typing import Mapping as TypeMap

from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.document.Validation.DistExtValidate import GetDistExtErrs
from interchange.Features.Distance.GetCutValues import GetCutValues
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# distance features require real sketches and cuts additionally require explicit body operands
def GetDistanceErrs(
    StepValue: FeatureStep,
    Definition: DistanceCut | DistanceExtrude,
    SketchIds: set[str],
    BodyIds: set[str],
    Parameters: TypeMap[str, Parameter],
) -> tuple[str, ...]:
    if isinstance(Definition, DistanceExtrude):
        return GetDistExtErrs(StepValue, Definition, SketchIds, Parameters)
    if (
        StepValue.sketch_id not in SketchIds
        or not set(Definition.TargetBodyIds) <= BodyIds
    ):
        return (f"distance cut {StepValue.id} has missing sketch or body operands",)
    try:
        _ = GetCutValues(StepValue, Definition, Parameters)
    except ValueError as ErrorInfo:
        return (f"distance cut {StepValue.id} is invalid: {ErrorInfo}",)
    return ()
