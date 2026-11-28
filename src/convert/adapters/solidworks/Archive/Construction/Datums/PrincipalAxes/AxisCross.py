from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)


# ordered native support roles determine the signed carrier of the through origin line
def AxisCross(First: KDatumVector, Other: KDatumVector) -> KDatumVector:
    FirstX, FirstY, FirstZ = First
    OtherX, OtherY, OtherZ = Other
    return (
        FirstY * OtherZ - FirstZ * OtherY,
        FirstZ * OtherX - FirstX * OtherZ,
        FirstX * OtherY - FirstY * OtherX,
    )
