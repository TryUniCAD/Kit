from fractions import Fraction
from itertools import combinations as DiskPairs

from convert.adapters.solidworks.Archive.Partition.LocalCylinder.BoreVectors import (
    BoreDelta,
    BoreDot,
    KBoreVec,
    MakeBoreVec,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)

# circular rims retain their spatial centre and radius on one proven common plane
KBoreRing = tuple[KPrismVector, float]

# exact arithmetic distinguishes touching and separated circles at either scale
KBoreDisk = tuple[KBoreVec, Fraction]


# compare the exact values that the model and transmit each represent
def MakeBoreDisk(RingValue: KBoreRing, Divisor: float) -> KBoreDisk:
    Centre, Radius = RingValue
    return MakeBoreVec(Centre, Divisor), Fraction(Radius / Divisor)


# squared transverse distance preserves tangency without a rounded square root
def DiskDistance(First: KBoreDisk, Second: KBoreDisk) -> Fraction:
    DeltaValue = BoreDelta(First[0], Second[0])
    return BoreDot(DeltaValue, DeltaValue)


# every opening must keep positive material around its wall in the represented units
def CheckBoreFit(
    OuterRing: KBoreRing, BoreRings: tuple[KBoreRing, ...], Divisor: float
) -> None:
    Stock = MakeBoreDisk(OuterRing, Divisor)
    Disks = tuple(MakeBoreDisk(RingValue, Divisor) for RingValue in BoreRings)
    if any(
        not 0 < Value[1] < Stock[1]
        or DiskDistance(Stock, Value) >= (Stock[1] - Value[1]) ** 2
        for Value in Disks
    ):
        raise ValueError("local circular bore does not clear the exterior wall")
    if any(
        DiskDistance(First, Second) <= (First[1] + Second[1]) ** 2
        for First, Second in DiskPairs(Disks, 2)
    ):
        raise ValueError("local circular bore openings overlap or touch")
