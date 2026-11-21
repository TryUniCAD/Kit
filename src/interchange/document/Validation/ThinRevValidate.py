from sys import float_info as FloatInfo
from typing import Mapping as TypeMap

from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.ThinRevolve import ThinRevolve
from interchange.Records.RecordParameter import Parameter
from interchange.document.Validation.AngleRevValidate import GetAngleRevErrs
from interchange.geometry.Models.Selection import Selection


# each authored wall must bind its actual positive driving length in neutral millimetres
def GetRevWall(
    StepValue: FeatureStep, ParameterId: str, Parameters: TypeMap[str, Parameter]
) -> float:
    ValueData = Parameters.get(ParameterId)
    if (
        ValueData is None
        or ValueData.owner_id != StepValue.id
        or ParameterId not in StepValue.parameter_ids
        or ValueData.role != ParameterRole.KDriving
        or ValueData.value.kind != ValueKind.KLength
        or ValueData.value.unit != "mm"
    ):
        raise ValueError("thin revolution wall requires an owned driving length in mm")
    LengthValue = ValueData.value.value
    if (
        not isinstance(LengthValue, (int, float))
        or isinstance(LengthValue, bool)
        or not 0.0 < LengthValue <= FloatInfo.max
    ):
        raise ValueError("thin revolution wall must be a positive finite length")
    return LengthValue


# the nested angular sweep and wall references share one containing feature
def GetThinRevErrs(
    StepValue: FeatureStep,
    Definition: ThinRevolve,
    Selections: TypeMap[str, Selection],
    Parameters: TypeMap[str, Parameter],
) -> tuple[str, ...]:
    Errors = list(
        GetAngleRevErrs(StepValue, Definition.SweepValue, Selections, Parameters)
    )
    for ParameterId in Definition.GetWallIds():
        try:
            _ = GetRevWall(StepValue, ParameterId, Parameters)
        except ValueError as ErrorInfo:
            Errors.append(f"thin revolution {StepValue.id}: {ErrorInfo}")
    return tuple(Errors)
