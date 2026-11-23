from convert.adapters.solidworks.Archive.Partition.LocalCylinder.BoreVectors import (
    BoreDelta,
    BoreDot,
    IsBoreParallel,
    KBoreVec,
    MakeBoreVec,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)


# two complete rims must remain on their actual cap stations and one shared wall axis
def CheckBorePair(
    CentresValue: tuple[KPrismVector, KPrismVector],
    CapOrigins: tuple[KPrismVector, KPrismVector],
    WallOrigin: KPrismVector,
    AxisValue: KBoreVec,
    Divisor: float,
) -> None:
    NearPoint, FarPoint = (MakeBoreVec(Value, Divisor) for Value in CentresValue)
    NearCap, FarCap = (MakeBoreVec(Value, Divisor) for Value in CapOrigins)
    if (
        WallOrigin not in CentresValue
        or BoreDot(AxisValue, BoreDelta(NearPoint, NearCap))
        or BoreDot(AxisValue, BoreDelta(FarPoint, FarCap))
        or not IsBoreParallel(AxisValue, BoreDelta(FarPoint, NearPoint))
    ):
        raise ValueError("local circular bore does not join its two exact cap stations")
