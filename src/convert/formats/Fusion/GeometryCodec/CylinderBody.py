from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite


@MakeDataClass(frozen=True, slots=True)
class CylinderBody:
    Radius: float
    Height: float
    BasePoint: tuple[float, float, float]

    def __post_init__(Model) -> None:
        if len(Model.BasePoint) != 3:
            raise ValueError("Cylinder base must have three millimetre coordinates")
        Values = (Model.Radius, Model.Height, *Model.BasePoint)
        if any(isinstance(Value, bool) or not IsFinite(Value) for Value in Values):
            raise ValueError("Cylinder dimensions must be finite real numbers")
        if Model.Radius <= 0 or Model.Height <= 0:
            raise ValueError("Cylinder radius and height must be positive")
        Limits = tuple(
            Coord + SignValue * Model.Radius
            for Coord in Model.BasePoint[:2]
            for SignValue in (-1, 1)
        ) + (Model.BasePoint[2] + Model.Height,)
        if not all(IsFinite(Value) for Value in Limits):
            raise ValueError("Cylinder dimensions exceed finite coordinate range")
        Bases = (
            (Model.BasePoint[0],) * 2
            + (Model.BasePoint[1],) * 2
            + (Model.BasePoint[2],)
        )
        if any(Value == Origin for Value, Origin in zip(Limits, Bases)):
            raise ValueError("Cylinder dimensions collapse at coordinate precision")
