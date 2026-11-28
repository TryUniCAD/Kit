from math import isfinite as IsFinite
from typing import cast as CastValue


# paper coordinates can arrive through wire input without runtime type checking
def IsFiniteMeasure(Value: object) -> bool:
    return (
        isinstance(Value, (int, float))
        and not isinstance(Value, bool)
        and IsFinite(Value)
    )


# positive rational scales must define a finite physical size
def IsValidRatio(Ratio: object) -> bool:
    if not isinstance(Ratio, tuple):
        return False
    Values = CastValue(tuple[object, ...], Ratio)
    return len(Values) == 2 and all(
        IsFiniteMeasure(Value) and CastValue(float, Value) > 0 for Value in Values
    )
