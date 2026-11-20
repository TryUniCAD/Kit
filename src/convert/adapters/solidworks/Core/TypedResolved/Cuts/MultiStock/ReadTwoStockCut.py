from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
    ReadStockOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockPick import (
    ReadStockPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
    ReadStockRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# typed lineage preserves the selected input and both surviving solids for later body binding
def ReadTwoStockCut(LinkValue: NativeLink) -> StockCutLineage:
    Features = ReadStockRoots(LinkValue)
    FirstStock, SecondStock, CutValue = ReadStockOps(LinkValue, Features)
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    FirstFrame, SecondFrame, CutFrame = (
        ReadPrismFrame(OwnerValue.ProfileValue, RootValue, Features, FrontOnly=False)
        for OwnerValue in (FirstStock, SecondStock, CutValue)
    )
    if FirstFrame == SecondFrame or CutFrame != FirstFrame:
        raise ValueError("two stock lineage has alternate signed profile placement")
    StockValues = (FirstStock, SecondStock)
    AtomsValue, Wrapper = ReadStockPick(LinkValue, StockValues, CutValue)
    return StockCutLineage(
        StockValues, CutValue, AtomsValue, Wrapper, (FirstFrame, SecondFrame, CutFrame)
    )
