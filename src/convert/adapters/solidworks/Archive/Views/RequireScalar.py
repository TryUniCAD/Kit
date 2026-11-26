from math import isfinite as IsFinite
from typing import cast as CastValue


# native view fields must reject boolean and nonfinite inputs before archive construction
def RequireScalar(NumberValue: object) -> float:
    if type(NumberValue) not in (int, float):
        raise TypeError("view coordinate or scale must be a real numeric value")
    ScalarValue = float(CastValue(float, NumberValue))
    if not IsFinite(ScalarValue):
        raise ValueError("view coordinate or scale must be finite")
    return ScalarValue
