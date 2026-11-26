from typing import cast as CastValue


# actual receipt objects are plain data without application callbacks
def ReadMeasMap(Value: object) -> dict[str, object]:
    if type(Value) is not dict or len(CastValue(dict[object, object], Value)) > 64:
        raise ValueError("native measurement requires an ordinary receipt object")
    return CastValue(dict[str, object], Value)
