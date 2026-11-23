from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    KStockBounds,
)


# only the witnessed interior rise produces this single front solid
def JoinSeedBounds(PlateBounds: KStockBounds, SeedBounds: KStockBounds) -> KStockBounds:
    PlateLow, PlateHigh = PlateBounds
    SeedLow, SeedHigh = SeedBounds
    if (
        PlateLow[2] != 0.0
        or SeedLow[2] != PlateLow[2]
        or not PlateHigh[2] < SeedHigh[2]
        or not all(
            PlateLow[AxisIndex]
            < SeedLow[AxisIndex]
            < SeedHigh[AxisIndex]
            < PlateHigh[AxisIndex]
            for AxisIndex in (0, 1)
        )
    ):
        raise ValueError(
            "expected a Front-plane plate and an interior raised seed with a common start"
        )
    return PlateLow, (PlateHigh[0], PlateHigh[1], SeedHigh[2])
