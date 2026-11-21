from typing import Mapping as TypeMap

from interchange.Features.Axes.AxisExtentConfig import MakeAxisView
from interchange.Features.Axes.SolveAxis import SolveAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter


# portable callers select the configuration and use the same solver as complete document validation
def ResolveAxis(
    StepValue: FeatureStep,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Parameters: TypeMap[str, Parameter],
    Configurations: tuple[Configuration, ...] = (),
) -> tuple[SpaceVector, SpaceVector] | None:
    return SolveAxis(
        StepValue, Selections, Frames, Parameters, MakeAxisView(Configurations)
    )
