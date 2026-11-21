from math import fsum as SumExact
from typing import Mapping as TypeMap

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.CheckAxisFit import CheckAxisFit
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.IntersectPlanes import GetPlaneLine
from interchange.Features.ReadAxisExtents import ReadAxisExtents
from interchange.Features.ReadAxisPlanes import ReadAxisPlanes
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter


# portable consumers must resolve the same current axis geometry that document validation checks
def ResolveAxis(
    StepValue: FeatureStep,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
    Parameters: TypeMap[str, Parameter],
) -> tuple[SpaceVector, SpaceVector]:
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
    Origin, Direction = GetPlaneLine(FirstPlane.transform, SecondPlane.transform)
    if isinstance(Definition, PlaneAxis):
        if StepValue.parameter_ids:
            raise ValueError("snapshot extent requires only its two plane selections")
        StartValue, EndValue = Definition.StartMm, Definition.EndMm
    else:
        Stations = ReadAxisExtents(StepValue, Definition, Parameters)
        StartValue, EndValue = (
            SpaceVector(
                *(
                    SumExact((Coordinate, Offset * Station))
                    for Coordinate, Offset in zip(Origin, Direction)
                )
            )
            for Station in Stations
        )
    CheckAxisFit(StartValue, EndValue, Origin, Direction)
    return StartValue, EndValue
