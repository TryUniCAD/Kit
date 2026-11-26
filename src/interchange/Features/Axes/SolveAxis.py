from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.Axes.AxisExtentConfig import (
    AxisConfigView,
    IsSuppressed,
    MakeAxisView,
)
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
from interchange.Records.RecordParameter import Parameter


# all bound axes in a complete document share one effective configuration view
def SolveAxis(
    StepValue: FeatureStep,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Parameters: TypeMap[str, Parameter],
    ConfigView: AxisConfigView | None,
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
        ViewValue = MakeAxisView(()) if ConfigView is None else ConfigView
        if ViewValue.ErrorText is not None:
            raise ValueError(ViewValue.ErrorText)
        Stations = ReadAxisExtents(StepValue, Definition, Parameters, ViewValue)
        if IsSuppressed(StepValue, ViewValue):
            return None
        Origin, Direction = GetPlaneLine(FirstFrame, SecondFrame)
        return MakeBoundAxis(Origin, Direction, Stations)
    if StepValue.parameter_ids:
        raise ValueError("snapshot extent requires only its two plane selections")
    Origin, Direction = GetPlaneLine(FirstFrame, SecondFrame)
    CheckAxisFit(Definition.StartMm, Definition.EndMm, Origin, Direction)
    return Definition.StartMm, Definition.EndMm
