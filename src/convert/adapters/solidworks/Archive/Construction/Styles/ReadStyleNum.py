from math import isfinite as IsFinite
from typing import cast as CastValue


# modeled numeric style settings must reject booleans nonfinite values and unsupported ranges before constructing archive fields
def ReadStyleNum(
    ValueInput: object, NameValue: str, LowerLimit: float | None = None
) -> float:
    if type(ValueInput) not in (int, float):
        raise ValueError(f"{NameValue} must be a finite authored number")
    try:
        NumberValue = float(CastValue(int | float, ValueInput))
    except (OverflowError, TypeError, ValueError) as ErrorValue:
        raise ValueError(
            f"{NameValue} must be a finite authored number"
        ) from ErrorValue
    if not IsFinite(NumberValue) or LowerLimit is not None and NumberValue < LowerLimit:
        raise ValueError(f"{NameValue} is outside its finite authored domain")
    return NumberValue
