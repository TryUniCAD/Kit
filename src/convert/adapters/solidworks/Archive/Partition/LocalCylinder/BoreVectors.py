from fractions import Fraction
from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)

# exact components preserve irreplaceable axial and transverse placement
KBoreVec = tuple[Fraction, Fraction, Fraction]


# the comparison must use the values that the selected unit system represents
def MakeBoreVec(PointValue: KPrismVector, Divisor: float = 1.0) -> KBoreVec:
    First, Second, Third = PointValue
    if not all(IsFinite(Value) for Value in PointValue):
        raise ValueError("local circular bore requires finite placement")
    return (
        Fraction(First / Divisor),
        Fraction(Second / Divisor),
        Fraction(Third / Divisor),
    )


# centre differences must stay exact even for a translated body
def BoreDelta(First: KBoreVec, Second: KBoreVec) -> KBoreVec:
    return First[0] - Second[0], First[1] - Second[1], First[2] - Second[2]


# disc incidence and squared distance share the same exact inner product
def BoreDot(First: KBoreVec, Second: KBoreVec) -> Fraction:
    return First[0] * Second[0] + First[1] * Second[1] + First[2] * Second[2]


# zero cross product proves parallelism without normalizing the represented axis
def IsBoreParallel(AxisValue: KBoreVec, SpanValue: KBoreVec) -> bool:
    AxisX, AxisY, AxisZ = AxisValue
    SpanX, SpanY, SpanZ = SpanValue
    return (
        any(AxisValue)
        and any(SpanValue)
        and AxisY * SpanZ == AxisZ * SpanY
        and AxisZ * SpanX == AxisX * SpanZ
        and AxisX * SpanY == AxisY * SpanX
    )
