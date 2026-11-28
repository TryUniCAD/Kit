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
        raise ValueError(f"chamfer requires its actual driving {NameValue} parameter")


# both mode groups require the same active feature and physical stock owner
def CheckChmfStep(
    StepValue: FeatureStep, PriorValue: FeatureStep
) -> ChamferFeature:
    Definition = StepValue.definition
    if (
        type(Definition) is not ChamferFeature
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
        raise ValueError("only one active chamfer on the preceding boss is supported")
    return Definition


# the existing angular mode keeps its original length and angular unit rules
def ReadAngleValues(
    StepValue: FeatureStep, Definition: ChamferFeature, Params: tuple[Parameter, ...]
) -> tuple[float, float]:
    if len(Params) != 2 or Definition.second_distance is not None or Definition.angle is None:
        raise ValueError("angle-distance chamfer needs a length and an angle")
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
    return DepthValue, AngleValue


# a shared setback owns one driver and separate setbacks retain their actual driver order
def ReadPairValues(
    StepValue: FeatureStep, Definition: ChamferFeature, Params: tuple[Parameter, ...]
) -> tuple[float, float | None]:
    EqualValue = Definition.mode == "equal_distance"
    if (
        Definition.angle is not None
        or len(Params) != (1 if EqualValue else 2)
        or (Definition.second_distance is None) != EqualValue
    ):
        raise ValueError("chamfer distance mode requires its exact independent driver count")
    Wanted = (Definition.distance,) if EqualValue else (Definition.distance, Definition.second_distance)
    Values: list[float] = []
    for Param, WantedValue, NameValue in zip(Params, Wanted, ("D1",) if EqualValue else ("D1", "D3"), strict=True):
        CheckChmfDriver(Param, StepValue.id, NameValue, ValueKind.KLength)
        if Param.value != WantedValue or Param.value.unit != "mm":
            raise ValueError("chamfer distance driver must retain its modeled millimetres")
        Values.append(RequireScalar(Param.value.value) / 1000.0)
    if min(Values) < 1e-14 or (not EqualValue and Values[0] == Values[1]):
        raise ValueError("distance chamfer needs positive setbacks and distinct independent values")
    return Values[0], None if EqualValue else Values[1]


# the fixed angle route stays public while the two measured source modes enter controlled construction
def ReadChmfValues(
    StepValue: FeatureStep,
    PriorValue: FeatureStep,
    Params: tuple[Parameter, ...],
    AllowDistancePair: bool,
) -> tuple[str, float, float | None, float | None]:
    Definition = CheckChmfStep(StepValue, PriorValue)
    NameValue = ReadStyleText(StepValue.name, "chamfer feature name")
    if Definition.mode == "distance_angle":
        Setback, Angle = ReadAngleValues(StepValue, Definition, Params)
        return NameValue, Setback, Angle, None
    if AllowDistancePair and Definition.mode in ("equal_distance", "two_distances"):
        Setback, OtherSetback = ReadPairValues(StepValue, Definition, Params)
        return NameValue, Setback, None, OtherSetback
    raise ValueError("only one active angle-distance chamfer on the preceding boss is supported")
