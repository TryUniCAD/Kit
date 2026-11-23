from fractions import Fraction
from itertools import combinations as DiskPairs

# transverse circles retain their two coordinates and authored radius
KBoreRing = tuple[float, float, float]

# exact arithmetic distinguishes touching and separated circles at either scale
KBoreDisk = tuple[Fraction, Fraction, Fraction]


# compare the exact values that the model and transmit each represent
def MakeBoreDisk(RingValue: KBoreRing, Divisor: float) -> KBoreDisk:
    First, Second, Radius = RingValue
    return (
        Fraction(First / Divisor),
        Fraction(Second / Divisor),
        Fraction(Radius / Divisor),
    )


# squared transverse distance preserves tangency without a rounded square root
def DiskDistance(First: KBoreDisk, Second: KBoreDisk) -> Fraction:
    return (First[0] - Second[0]) ** 2 + (First[1] - Second[1]) ** 2


# every opening must keep positive material around its wall in the represented units
def CheckBoreFit(
    OuterRing: KBoreRing, BoreRings: tuple[KBoreRing, ...], Divisor: float
) -> None:
    Stock = MakeBoreDisk(OuterRing, Divisor)
    Disks = tuple(MakeBoreDisk(RingValue, Divisor) for RingValue in BoreRings)
    if any(
        not 0 < Value[2] < Stock[2]
        or DiskDistance(Stock, Value) >= (Stock[2] - Value[2]) ** 2
        for Value in Disks
    ):
        raise ValueError("local circular bore does not clear the exterior wall")
    if any(
        DiskDistance(First, Second) <= (First[2] + Second[2]) ** 2
        for First, Second in DiskPairs(Disks, 2)
    ):
        raise ValueError("local circular bore openings overlap or touch")
