from math import isfinite as IsFinite, sqrt as SquareRoot
from typing import TypeAlias

# archive point calculations share one explicit three coordinate representation
KDatumVector: TypeAlias = tuple[float, float, float]


# the through origin canonical hinge points down the shared top and right intersection
KHingeAxis: KDatumVector = (0.0, 0.0, -1.0)


# the measured angular branch uses the world origin as its coincident anchor
KHingeRoot: KDatumVector = (0.0, 0.0, 0.0)


# ordered additions retain the native rounding of the datum and display records
def DatumDot(First: KDatumVector, Other: KDatumVector) -> float:
    return (First[0] * Other[0] + First[1] * Other[1]) + First[2] * Other[2]


# the native normalizer multiplies each component by the same reciprocal length
def DatumUnit(Vector: KDatumVector) -> KDatumVector:
    LengthSquared = DatumDot(Vector, Vector)
    if not IsFinite(LengthSquared) or LengthSquared < 1e-17:
        raise ValueError("datum direction requires a finite nondegenerate vector")
    Inverse = 1.0 / SquareRoot(LengthSquared)
    return (Inverse * Vector[0], Inverse * Vector[1], Inverse * Vector[2])


# each offset applies one modeled direction from the actual base point
def DatumOffset(
    Origin: KDatumVector, Vector: KDatumVector, Distance: float
) -> KDatumVector:
    return (
        Origin[0] + Vector[0] * Distance,
        Origin[1] + Vector[1] * Distance,
        Origin[2] + Vector[2] * Distance,
    )


# ordered difference retains the locally transformed geometric witnesses
def DatumDiff(First: KDatumVector, Other: KDatumVector) -> KDatumVector:
    return (First[0] - Other[0], First[1] - Other[1], First[2] - Other[2])


# independent point records must keep distinct mutable field mappings
def DatumPoint(Vector: KDatumVector) -> dict[str, float]:
    return {"x": Vector[0], "y": Vector[1], "z": Vector[2]}
