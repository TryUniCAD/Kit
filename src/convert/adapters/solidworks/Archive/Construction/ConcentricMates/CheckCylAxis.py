from math import fsum as SumValues, isclose as IsClose, isfinite as IsFinite
from typing import cast as CastValue


# the requested child local axis can oppose the carrier while remaining on its actual line
def CheckCylAxis(
    AxisValue: tuple[float, float, float], Carrier: tuple[float, float, float]
) -> tuple[float, float, float]:
    Members = CastValue(tuple[object, ...], AxisValue)
    if (
        type(CastValue(object, AxisValue)) is not tuple
        or len(Members) != 3
        or any(
            type(Value) not in (int, float) or not IsFinite(CastValue(float, Value))
            for Value in Members
        )
    ):
        raise ValueError("concentric child-local axis requires three finite scalars")
    SignValue = (
        -1.0
        if SumValues(
            Value * Other for Value, Other in zip(AxisValue, Carrier, strict=True)
        )
        < 0.0
        else 1.0
    )
    if not IsClose(
        SumValues(Value * Value for Value in AxisValue),
        1.0,
        rel_tol=1e-10,
        abs_tol=1e-12,
    ) or not all(
        IsClose(Value, SignValue * Other, rel_tol=1e-10, abs_tol=1e-12)
        for Value, Other in zip(AxisValue, Carrier, strict=True)
    ):
        raise ValueError(
            "concentric child-local axis must be a unit direction on the actual carrier"
        )
    return float(AxisValue[0]), float(AxisValue[1]), float(AxisValue[2])
