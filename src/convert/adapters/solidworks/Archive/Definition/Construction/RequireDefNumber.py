from math import isfinite as IsFinite


# authored doubles must be finite native values before any record is constructed
def RequireDefNum(Value: object) -> float:
    if isinstance(Value, bool) or not isinstance(Value, (int, float)):
        raise TypeError("SOLIDWORKS document settings require a real numeric value")
    try:
        NativeValue = float(Value)
    except OverflowError as ErrorInfo:
        raise ValueError(
            "SOLIDWORKS document setting exceeds the double domain"
        ) from ErrorInfo
    if not IsFinite(NativeValue):
        raise ValueError("SOLIDWORKS document setting must be finite")
    return NativeValue
