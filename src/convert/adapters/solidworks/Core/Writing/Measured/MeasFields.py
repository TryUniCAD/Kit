from re import fullmatch as FullMatch
from typing import cast as CastValue

# native evidence belongs to the caller rather than authored neutral model metadata
KPartMeasureOpt = "solidworks_native_measurement"


# actual receipt objects are plain data without application callbacks
def ReadMeasMap(Value: object) -> dict[str, object]:
    if type(Value) is not dict or len(CastValue(dict[object, object], Value)) > 64:
        raise ValueError("native measurement requires an ordinary receipt object")
    return CastValue(dict[str, object], Value)


# bounded receipt rows keep validation independent of any measurement resource
def ReadMeasRows(Value: object, Limit: int = 256) -> tuple[dict[str, object], ...]:
    if type(Value) is not list or len(CastValue(list[object], Value)) > Limit:
        raise ValueError("native measurement requires bounded receipt rows")
    return tuple(ReadMeasMap(ItemValue) for ItemValue in CastValue(list[object], Value))


# a digest must have its canonical complete hexadecimal representation
def ReadMeasSha(Value: object) -> str:
    if type(Value) is not str or FullMatch(r"[0-9a-f]{64}", Value) is None:
        raise ValueError("native measurement requires a canonical SHA-256")
    return Value


# the receipt must report a real positive count or measurement of the observed model
def ReadMeasNum(Value: object) -> float:
    if (
        not isinstance(Value, (int, float))
        or isinstance(Value, bool)
        or not 0 < Value < float("inf")
    ):
        raise ValueError("native measurement requires positive finite observations")
    return float(Value)
