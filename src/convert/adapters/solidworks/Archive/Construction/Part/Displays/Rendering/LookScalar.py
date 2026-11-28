from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar


# appearance arithmetic must round at the native float operation boundaries
def LookScalar(NumberValue: float, LowValue: float, HighValue: float) -> float:
    if (
        type(CastValue(object, NumberValue)) not in (int, float)
        or not IsFinite(NumberValue)
        or not LowValue <= NumberValue <= HighValue
    ):
        raise ValueError("appearance scalar lies outside its supported domain")
    return float(ReadScalar(EncodeScalar(NumberValue, "f32"), 0, "f32")[0])
