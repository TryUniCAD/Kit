from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum


# every observed state includes mass volume area and all three signed centre components
def ReadRevMass(Value: object) -> tuple[float, float, float, float, float, float]:
    RowValue = ReadMeasMap(Value)
    Centre = RowValue.get("com")
    if type(Centre) is not list:
        raise ValueError("measured revolve requires a finite centre of mass")
    Coordinates = CastValue(list[int | float], Centre)
    if len(Coordinates) != 3 or any(type(Number) not in (int, float) or not IsFinite(Number) for Number in Coordinates):
        raise ValueError("measured revolve requires a finite centre of mass")
    return (
        ReadMeasNum(RowValue.get("mass")),
        ReadMeasNum(RowValue.get("volume")),
        ReadMeasNum(RowValue.get("area")),
        float(Coordinates[0]),
        float(Coordinates[1]),
        float(Coordinates[2]),
    )
