from dataclasses import dataclass as DataClass
from math import isclose as IsClose, isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum


# positive masses and editable values belong to one observed native state
@DataClass(frozen=True, slots=True)
class CircState:
    CenterValue: tuple[float, ...]
    RadialValue: float
    DepthValue: float
    VolumeValue: float
    AreaValue: float
    CentroidValue: tuple[float, ...]


# coordinates permit signed zero and finite numeric words only
def CircCoordinate(Value: object) -> float:
    if type(Value) not in (int, float):
        raise ValueError("circle native coordinate is not a real numeric value")
    Number = float(CastValue(int | float, Value))
    if not IsFinite(Number):
        raise ValueError("circle native coordinate is not finite")
    return Number


# coordinate rows are finite observations in their declared number of axes
def ReadCircVec(Value: object, Count: int) -> tuple[float, ...]:
    if type(Value) is not list or len(CastValue(list[object], Value)) != Count:
        raise ValueError("circle native coordinates require their actual dimension")
    return tuple(
        CircCoordinate(ItemValue) for ItemValue in CastValue(list[object], Value)
    )


# six significant figures compare native mass properties with the prospective model prediction
def ReadCircMass(StateValue: dict[str, object]) -> dict[str, object]:
    Actual = ReadMeasMap(StateValue.get("mass_properties"))
    Predicted = ReadMeasMap(StateValue.get("expected_mass_properties"))
    Scalars = (
        "volume",
        "area",
        "mass_kg",
        "effective_density_kg_m3",
        "document_density_kg_m3",
    )
    for NameValue in Scalars:
        if not IsClose(
            ReadMeasNum(Actual.get(NameValue)),
            ReadMeasNum(Predicted.get(NameValue)),
            rel_tol=5e-6,
        ):
            raise ValueError(
                "circle native scalar measurement differs from its prediction"
            )
    ActualCom, PredictedCom = (
        ReadCircVec(RowValue.get("com"), 3) for RowValue in (Actual, Predicted)
    )
    if any(
        not IsClose(ActualValue, TargetValue, rel_tol=5e-6, abs_tol=1e-12)
        for ActualValue, TargetValue in zip(ActualCom, PredictedCom, strict=True)
    ):
        raise ValueError("circle native centroid differs from its prediction")
    return Actual


# a complete stage requires both edit drivers and actual physically measured body state
def ReadCircState(Stage: dict[str, object], NameValue: str) -> CircState:
    Snapshots = ReadMeasMap(Stage.get("snapshots"))
    StateValue = ReadMeasMap(Snapshots.get(NameValue))
    if StateValue.get("fully_constrained") is not True:
        raise ValueError(
            "circle native sketch did not retain its driving and fixed relations"
        )
    MassValue = ReadCircMass(StateValue)
    return CircState(
        ReadCircVec(StateValue.get("center_m"), 2),
        ReadMeasNum(StateValue.get("driving_radial_m")),
        ReadMeasNum(StateValue.get("driving_depth_m")),
        ReadMeasNum(MassValue.get("volume")),
        ReadMeasNum(MassValue.get("area")),
        ReadCircVec(MassValue.get("com"), 3),
    )
