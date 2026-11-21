from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.Axes.AxisConfigChain import GetAxisConfigs
from interchange.Features.Axes.AxisExtentConfig import IsSuppressed
from interchange.Features.Axes.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.Axes.IntersectPlanes import GetAxisFrame, GetPlaneLine
from interchange.Features.Axes.MakeBoundAxis import MakeBoundAxis
from interchange.Features.Axes.ReadAxisExtents import ReadAxisExtents
from interchange.Features.Axes.ReadAxisPlanes import ReadAxisPlanes
from interchange.Features.CheckAxisFit import CheckAxisFit
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter


# portable consumers must resolve the same current axis geometry that document validation checks
def ResolveAxis(
    StepValue: FeatureStep,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Parameters: TypeMap[str, Parameter],
    Configurations: tuple[Configuration, ...] = (),
) -> tuple[SpaceVector, SpaceVector] | None:
    Definition = StepValue.definition
    if (
        not isinstance(Definition, (PlaneAxis, BoundPlaneAxis))
        or StepValue.kind != FeatureKind.KReference
        or StepValue.sketch_id is not None
        or StepValue.operation is not None
    ):
        raise ValueError("requires a reference feature with plane selections")
    PickIds = (Definition.FirstPlaneSelectionId, Definition.SecondPlaneSelectionId)
    FirstPlane, SecondPlane = ReadAxisPlanes(StepValue, PickIds, Selections, Frames)
    FirstFrame, SecondFrame = (
        GetAxisFrame(FirstPlane.transform),
        GetAxisFrame(SecondPlane.transform),
    )
    if isinstance(Definition, BoundPlaneAxis):
        Chain = GetAxisConfigs(Configurations)
        Stations = ReadAxisExtents(StepValue, Definition, Parameters, Chain)
        if IsSuppressed(StepValue, Chain):
            return None
        Origin, Direction = GetPlaneLine(FirstFrame, SecondFrame)
        return MakeBoundAxis(Origin, Direction, Stations)
    if StepValue.parameter_ids:
        raise ValueError("snapshot extent requires only its two plane selections")
    Origin, Direction = GetPlaneLine(FirstFrame, SecondFrame)
    CheckAxisFit(Definition.StartMm, Definition.EndMm, Origin, Direction)
    return Definition.StartMm, Definition.EndMm
