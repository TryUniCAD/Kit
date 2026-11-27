from math import isfinite as IsFinite


# scalar conversion keeps invalid receipt numbers on the normal refusal path
def ReadMeasReal(Value: object) -> float:
    if not isinstance(Value, (int, float)) or isinstance(Value, bool):
        raise ValueError("native measurement requires finite scalar observations")
    try:
        NumberValue = float(Value)
    except OverflowError as ErrorInfo:
        raise ValueError(
            "native measurement requires finite scalar observations"
        ) from ErrorInfo
    if not IsFinite(NumberValue):
        raise ValueError("native measurement requires finite scalar observations")
    return NumberValue
