from math import isfinite as IsFinite
from string import hexdigits as KHexDigits
from typing import cast as CastValue


# measurement maps must contain concrete offline values rather than custom mapping behavior
def ReadMeasMap(Value: object) -> dict[str, object]:
    if type(Value) is not dict:
        raise ValueError("Fusion measurement record must be an object")
    return CastValue(dict[str, object], Value)


# positive process identifiers distinguish independently opened oracle sessions
def ReadMeasPid(Value: object) -> int:
    if type(Value) is not int or Value <= 0:
        raise ValueError("Fusion measurement process ID is invalid")
    return Value


# candidate and stage identities must be complete digests
def ReadMeasSha(Value: object) -> str:
    if (
        not isinstance(Value, str)
        or len(Value) != 64
        or any(Digit not in KHexDigits for Digit in Value)
    ):
        raise ValueError("Fusion measurement digest is invalid")
    return Value


# finite observations exclude boolean values and nonnumeric or unmeasurable geometry
def ReadMeasNum(Value: object) -> float:
    if type(Value) not in (float, int):
        raise ValueError("Fusion measurement requires a finite number")
    try:
        Number = float(CastValue(float, Value))
    except OverflowError as ErrorInfo:
        raise ValueError("Fusion measurement requires a finite number") from ErrorInfo
    if not IsFinite(Number):
        raise ValueError("Fusion measurement requires a finite number")
    return Number


# measurement inventories must contain explicit rows so empty results cannot qualify
def ReadMeasList(Value: object) -> list[object]:
    if type(Value) is not list or not Value:
        raise ValueError("Fusion measurement requires a nonempty inventory")
    return CastValue(list[object], Value)
