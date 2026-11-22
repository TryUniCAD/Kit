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


# only the measured linear distance modes have a public preparation path
def ReadChmfValues(
    StepValue: FeatureStep,
    PriorValue: FeatureStep,
    Params: tuple[Parameter, ...],
) -> tuple[str, float, float | None]:
    Definition = CheckChmfStep(StepValue, PriorValue)
    if Definition.mode not in ("equal_distance", "two_distances"):
        raise ValueError("only ordinary equal or two-distance chamfers are supported")
    NameValue = ReadStyleText(StepValue.name, "chamfer feature name")
    Setback, OtherSetback = ReadPairValues(StepValue, Definition, Params)
    return NameValue, Setback, OtherSetback
