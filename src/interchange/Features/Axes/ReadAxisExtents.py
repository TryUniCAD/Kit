from typing import Mapping as TypeMap

from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.Axes.AxisExtentConfig import ConfigAxisParam
from interchange.Features.Axes.BoundPlaneAxis import BoundPlaneAxis
from interchange.Features.DistanceParam import GetDistParam
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter


# literal stations must be editable bindings on the exact feature that owns the finite line
def ReadAxisExtents(
    StepValue: FeatureStep,
    Definition: BoundPlaneAxis,
    Parameters: TypeMap[str, Parameter],
    Chain: tuple[Configuration, ...],
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
        Effective = ConfigAxisParam(Param, Chain)
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
