from typing import Mapping as TypeMap

from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Axes.ResolveAxis import ResolveAxis
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


# only the owning feature can identify the actual ordered plane selections in its document
def GetAxisErrors(
    StepValue: FeatureStep,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Parameters: TypeMap[str, Parameter],
) -> tuple[str, ...]:
    try:
        _ = ResolveAxis(StepValue, Selections, Frames, Parameters)
    except (ValueError, OverflowError) as ErrorInfo:
        return (f"plane axis {StepValue.id}: {ErrorInfo}",)
    return ()
