from math import fsum as SumValues
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CheckCylAxis import (
    CheckCylAxis,
)


# both ordered selections on the one shared child must retain a consistent local direction
def GetCylAxes(
    Carrier: tuple[float, float, float],
    AxesValue: tuple[tuple[float, float, float], tuple[float, float, float]] | None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if AxesValue is None:
        return Carrier, Carrier
    if type(CastValue(object, AxesValue)) is not tuple or len(AxesValue) != 2:
        raise ValueError("concentric mate requires two ordered child-local axes")
    First = CheckCylAxis(AxesValue[0], Carrier)
    Second = CheckCylAxis(AxesValue[1], Carrier)
    if (
        SumValues(Value * Other for Value, Other in zip(First, Second, strict=True))
        <= 0.0
    ):
        raise ValueError("concentric endpoint axes disagree on the same child cylinder")
    return First, Second
