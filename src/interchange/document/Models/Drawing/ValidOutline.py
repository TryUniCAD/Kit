from typing import cast as CastValue

from interchange.document.Models.Drawing.ValidMeasure import IsFiniteMeasure


# consumers need finite ordered bounds when a native view exposes its outline
def IsValidOutline(Outline: object) -> bool:
    if not isinstance(Outline, tuple):
        return False
    Values = CastValue(tuple[object, ...], Outline)
    if len(Values) != 4 or not all(IsFiniteMeasure(Value) for Value in Values):
        return False
    LowerX, LowerY, UpperX, UpperY = CastValue(
        tuple[float, float, float, float], Values
    )
    return LowerX <= UpperX and LowerY <= UpperY
