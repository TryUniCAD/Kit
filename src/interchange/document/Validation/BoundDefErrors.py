from typing import Mapping as TypeMap

from interchange.document.Validation.BoundPlaneValidate import CheckBoundPlane
from interchange.Features.BoundScaleValues import GetScaleValues
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeatureBoundScale import BoundScale
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtValues import GetPlaneExt
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# selected support definitions retain their existing validation as feature dispatch grows
def GetBoundErrors(
    StepValue: FeatureStep,
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Sketches: TypeMap[str, Sketch],
) -> tuple[str, ...]:
    Definition = StepValue.definition
    Label = (
        "construction plane"
        if isinstance(Definition, BoundDatum)
        else "scale" if isinstance(Definition, BoundScale) else "plane extrusion"
    )
    try:
        if isinstance(Definition, BoundDatum):
            CheckBoundPlane(StepValue, Definition, Parameters, Frames)
        elif isinstance(Definition, BoundScale):
            _ = GetScaleValues(StepValue, Definition, Parameters, Selections)
        elif isinstance(Definition, PlaneExtrude):
            _ = GetPlaneExt(
                StepValue, Definition, Parameters, Selections, Frames, Sketches
            )
    except ValueError as ErrorInfo:
        return (f"{Label} {StepValue.id} is invalid: {ErrorInfo}",)
    return ()
