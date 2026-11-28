from math import isclose as IsClose

from convert.adapters.Fusion.Measurement.ReadFuseMeas import (
    ReadMeasList,
    ReadMeasMap,
    ReadMeasNum,
)


# the oracle records centimetres so its absolute position tolerance scales to millimetres
def IsSamePoint(First: object, Second: object) -> bool:
    FirstValues = ReadMeasList(First)
    Right = ReadMeasList(Second)
    return len(FirstValues) == len(Right) == 3 and all(
        IsClose(ReadMeasNum(AxisA), ReadMeasNum(AxisB), rel_tol=1e-8, abs_tol=1e-7)
        for AxisA, AxisB in zip(FirstValues, Right, strict=True)
    )


# body topology and identity stay exact while measured positions and volume use oracle tolerances
def IsSameBody(First: dict[str, object], Second: dict[str, object]) -> bool:
    BoundsA = ReadMeasList(First.get("bounds_mm"))
    BoundsB = ReadMeasList(Second.get("bounds_mm"))
    return (
        all(
            First[KeyText] == Second[KeyText]
            for KeyText in ("name", "faces", "edges", "vertices")
        )
        and IsClose(
            ReadMeasNum(First.get("volume_mm3")),
            ReadMeasNum(Second.get("volume_mm3")),
            rel_tol=1e-8,
            abs_tol=1e-5,
        )
        and IsSamePoint(First.get("center_mm"), Second.get("center_mm"))
        and len(BoundsA) == len(BoundsB) == 2
        and all(
            IsSamePoint(PointA, PointB)
            for PointA, PointB in zip(BoundsA, BoundsB, strict=True)
        )
    )


# this receipt schema reports independently measured geometry for one cuboid solid
def IsFuseGeom(First: object, Second: object) -> bool:
    FirstValues = ReadMeasList(First)
    Right = ReadMeasList(Second)
    return len(FirstValues) == len(Right) == 1 and IsSameBody(
        ReadMeasMap(FirstValues[0]), ReadMeasMap(Right[0])
    )
