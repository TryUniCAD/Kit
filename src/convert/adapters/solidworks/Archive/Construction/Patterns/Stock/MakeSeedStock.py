from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    FrontStockBox,
    KStockBounds,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)


# the merged profile needs its own four oriented edges and independent forward blind driver
def MakeSeedStock(
    InputValue: SeedStockInput, BoxValue: FrontStockBox, BoundsValue: KStockBounds
) -> ThroughStock:
    (LeftX, LowerY, _), (RightX, UpperY, DepthValue) = BoundsValue
    return ThroughStock(
        InputValue.NameValue,
        InputValue.ConfigName,
        "Front Plane",
        BoxValue.SketchName,
        BoxValue.SketchName,
        BoxValue.FeatureName,
        BoxValue.FeatureName,
        f"D1@{BoxValue.FeatureName}",
        f"Body@{BoxValue.FeatureName}",
        ((LeftX, LowerY), (RightX, LowerY), (RightX, UpperY), (LeftX, UpperY)),
        DepthValue,
        RightX - LeftX,
        UpperY - LowerY,
        "z",
    )
