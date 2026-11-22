from math import pi as PiValue, radians as Radians

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureKinds import ChamferFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# an explicit chamfer driver must retain its real feature binding and length or angle kind
def CheckChmfDriver(
    ParamValue: Parameter, OwnerId: str, NameValue: str, KindValue: ValueKind
) -> None:
    if (
        ParamValue.name != NameValue
        or ParamValue.owner_id != OwnerId
        or ParamValue.role != ParameterRole.KDriving
        or ParamValue.expression is not None
        or ParamValue.attributes
        or ParamValue.value.kind != KindValue
    ):
        raise ValueError("chamfer requires actual distinct driving D1 and D2")


# a chamfer plan keeps both ordered controls and refuses every unmeasured operation mode
def ReadChmfValues(
    StepValue: FeatureStep, PriorValue: FeatureStep, Params: tuple[Parameter, Parameter]
) -> tuple[str, float, float]:
    Definition = StepValue.definition
    if (
        type(Definition) is not ChamferFeature
        or Definition.mode != "distance_angle"
        or Definition.second_distance is not None
        or Definition.angle is None
        or StepValue.kind != FeatureKind.KChamfer
        or StepValue.operation is not None
        and StepValue.operation != BooleanOp.KCutOperation
        or StepValue.order <= PriorValue.order
        or StepValue.input_feature_ids != (PriorValue.id,)
        or StepValue.sketch_id is not None
        or StepValue.suppressed
        or StepValue.configuration_states
        or StepValue.attributes
    ):
        raise ValueError(
            "only one active angle-distance chamfer on the preceding boss is supported"
        )
    Distance, Angle = Params
    CheckChmfDriver(Distance, StepValue.id, "D1", ValueKind.KLength)
    CheckChmfDriver(Angle, StepValue.id, "D2", ValueKind.KAngle)
    if (
        StepValue.parameter_ids != (Distance.id, Angle.id)
        or Distance.value != Definition.distance
        or Angle.value != Definition.angle
        or Distance.value.unit != "mm"
        or Angle.value.unit not in ("degree", "deg", "rad")
    ):
        raise ValueError(
            "chamfer driver values or explicit length and angle units disagree"
        )
    DepthValue = RequireScalar(Distance.value.value) / 1000.0
    AngleValue = RequireScalar(Angle.value.value)
    if Angle.value.unit != "rad":
        AngleValue = Radians(AngleValue)
    if DepthValue < 1e-14 or not 0.0 < AngleValue < PiValue / 2:
        raise ValueError("chamfer requires a positive distance and an acute angle")
    return ReadStyleText(StepValue.name, "chamfer feature name"), DepthValue, AngleValue
