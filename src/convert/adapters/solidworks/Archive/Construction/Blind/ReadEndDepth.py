from math import isfinite as IsFinite
from typing import cast as CastValue


# every active native boss direction must have a finite positive model length before a dimension is allocated
def ReadEndDepth(DepthValue: float) -> float:
    if type(CastValue(object, DepthValue)) not in (int, float):
        raise TypeError("boss depth must be a real numeric input")
    try:
        NativeValue = float(DepthValue)
    except OverflowError as ErrorInfo:
        raise ValueError("boss depth exceeds the native numeric domain") from ErrorInfo
    if not IsFinite(NativeValue) or NativeValue < 1e-14:
        raise ValueError("boss depth must be finite and at least 1e-14 metres")
    return NativeValue
