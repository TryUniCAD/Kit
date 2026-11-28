from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadFaceRing import (
    KPrismRing,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)


# each solid box or cavity supplies its directed floor rim and four connected walls
def PocketRings(
    Minimum: KPrismVector, Maximum: KPrismVector, *, Cavity: bool
) -> tuple[KPrismRing, KPrismRing, tuple[KPrismRing, ...]]:
    LowerX, LowerY, LowerZ = Minimum
    UpperX, UpperY, UpperZ = Maximum
    Footprint = ((LowerX, LowerY), (UpperX, LowerY), (UpperX, UpperY), (LowerX, UpperY))
    Lower = tuple((*Corner, LowerZ) for Corner in Footprint)
    Upper = tuple((*Corner, UpperZ) for Corner in Footprint)
    Walls = tuple(
        (Lower[Index], Lower[Following], Upper[Following], Upper[Index])
        for Index in range(4)
        for Following in ((Index + 1) % 4,)
    )
    if Cavity:
        return Lower, Upper[::-1], tuple(Value[::-1] for Value in Walls)
    return Lower[::-1], Upper, Walls
