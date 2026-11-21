from typing import Mapping as TypeMap

from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.Axes.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# literal stations must be editable bindings on the exact feature that owns the finite line
def ReadAxisExtents(
    StepValue: FeatureStep,
    Definition: BoundPlaneAxis,
    Parameters: TypeMap[str, Parameter],
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
            or Param.expression is not None
        ):
            raise ValueError(
                "requires editable literal length parameters for its extents"
            )
        try:
            Extents.append(
                GetDistParam(StepValue, Identity, Parameters, ValueKind.KLength)
            )
        except ValueError as ErrorInfo:
            raise ValueError(
                "requires owned finite length parameters for its extents"
            ) from ErrorInfo
    StartValue, EndValue = Extents
    return StartValue, EndValue
