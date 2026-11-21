from typing import Mapping as TypeMap

from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.Axes.AxisExtentConfig import AxisConfigView, ConfigAxisParam
from interchange.Features.Axes.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# stations retain evaluated values and driving ownership on the exact finite axis feature
def ReadAxisExtents(
    StepValue: FeatureStep,
    Definition: BoundPlaneAxis,
    Parameters: TypeMap[str, Parameter],
    ViewValue: AxisConfigView,
) -> tuple[float, float]:
    ParamIds = (Definition.StartParameterId, Definition.EndParameterId)
    if StepValue.parameter_ids != ParamIds:
        raise ValueError("has inconsistent ordered extent parameter roles")
    Extents: list[float] = []
    for Identity in ParamIds:
        Param = Parameters.get(Identity)
        if (
            Param is None
            or Param.id != Identity
            or Param.role != ParameterRole.KDriving
        ):
            raise ValueError(
                "requires editable driving length parameters for its extents"
            )
        Effective = ConfigAxisParam(Param, ViewValue)
        try:
            Length = GetDistParam(StepValue, Identity, Parameters, ValueKind.KLength)
            if Effective is not Param:
                Length = GetDistParam(
                    StepValue, Identity, {Identity: Effective}, ValueKind.KLength
                )
        except ValueError as ErrorInfo:
            raise ValueError(
                "requires owned finite length parameters for its extents"
            ) from ErrorInfo
        Extents.append(Length)
    StartValue, EndValue = Extents
    return StartValue, EndValue
