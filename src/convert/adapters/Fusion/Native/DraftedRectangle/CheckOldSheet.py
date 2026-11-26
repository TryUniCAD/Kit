from itertools import product as GridPoints

from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import CheckRegionTags
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegion import (
    CheckRegion,
)


# retired sheets preserve their original anchored footprint and selected source curve tags
def CheckOldSheet(
    Region: RegionFrame, Curves: dict[int, frozenset[tuple[float, float]]]
) -> None:
    CheckRegion(Region, Region.CornersCm)
    Width = max(Point[0] for Point in Region.CornersCm)
    Depth = max(Point[1] for Point in Region.CornersCm)
    if min(Width, Depth) <= 0 or set(Region.CornersCm) != set(
        GridPoints((0.0, Width), (0.0, Depth), (0.0,))
    ):
        raise ValueError("Native retired sketch sheet is not an anchored XY rectangle")
    CheckRegionTags(
        Region,
        {
            CurveTag: frozenset(
                (Width if XValue > 0 else 0.0, Depth if YValue > 0 else 0.0)
                for XValue, YValue in Points
            )
            for CurveTag, Points in Curves.items()
        },
    )
