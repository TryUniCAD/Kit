from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDiff,
    DatumDot,
    DatumUnit,
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)


# the actual selected rectangle supplies an ordered midpoint and displacement for its normal line
def DatumLine(
    FrameValue: PlaneFrame, Borders: tuple[float, float, float, float]
) -> tuple[KDatumVector, KDatumVector, float]:
    Origin = FrameValue.OriginValue
    Horizontal, Normal = FrameValue.AxisU, FrameValue.NormalValue
    if (
        not all(IsFinite(Value) for Value in Origin)
        or abs(DatumDot(Horizontal, Horizontal) - 1.0) > 1e-14
        or abs(DatumDot(Normal, Normal) - 1.0) > 1e-14
        or abs(DatumDot(Horizontal, Normal)) > 1e-14
    ):
        raise ValueError("datum line requires a finite orthonormal selected frame")
    UpperU, LowerU, UpperV, LowerV = Borders
    if not all(IsFinite(Value) for Value in Borders) or not (
        UpperU > LowerU and UpperV > LowerV
    ):
        raise ValueError("datum display requires two finite positive spans")
    Vertical = DatumUnit(CrossVector(Normal, Horizontal))
    Perimeter = ((LowerU, UpperV), (UpperU, UpperV), (UpperU, LowerV), (LowerU, LowerV))
    CenterParts: list[float] = []
    for OriginValue, AxisU, AxisV in zip(Origin, Horizontal, Vertical, strict=True):
        First, Second, Third, LastValue = (
            OriginValue + (ScaleU * AxisU + ScaleV * AxisV)
            for ScaleU, ScaleV in Perimeter
        )
        CenterParts.append(((((0.0 + First) + Second) + Third) + LastValue) * 0.25)
    Center = (CenterParts[0], CenterParts[1], CenterParts[2])
    NextPoint = (Center[0] + Normal[0], Center[1] + Normal[1], Center[2] + Normal[2])
    Displacement = DatumDiff(NextPoint, Center)
    Direction = DatumUnit(Displacement)
    return Center, Direction, DatumDot(Displacement, Direction)
