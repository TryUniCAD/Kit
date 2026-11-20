from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.CheckColdDepth import (
    CheckColdDepth,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.CheckColdState import (
    CheckColdState,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdAtoms import (
    ReadColdAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdFrames import (
    ReadColdFrames,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdSelect import (
    ReadColdSelect,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
    ReadStockOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
    ReadStockRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# every cold owner must come from the same actual linked versioned archive
def ReadColdOwners(LinkValue: NativeLink) -> ColdStockOwners:
    if LinkValue.ResolvedValue.ExtraFields is not None:
        raise ValueError("provisional two-stock ownership excludes a resolved body map")
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Features = ReadStockRoots(LinkValue)
    OwnersValue = ReadStockOps(LinkValue, Features)
    FirstStock, SecondStock, CutValue = OwnersValue
    StockValues = (FirstStock, SecondStock)
    CheckColdState(OwnersValue)
    StockAtoms, AtomIds = ReadColdAtoms(LinkValue, StockValues)
    Selected, WrapperValue = ReadColdSelect(LinkValue, OwnersValue, AtomIds)
    for OwnerValue in StockValues:
        CheckColdDepth(LinkValue, OwnerValue)
    FramesValue = ReadColdFrames(LinkValue, OwnersValue, Features, Selected)
    CheckTreeAlias(
        LinkValue,
        (
            RootValue,
            *StockAtoms,
            *(Value.NodeValue for Value in OwnersValue),
            *(Value.ProfileValue for Value in OwnersValue),
            *(Value.EndValue for Value in OwnersValue),
        ),
    )
    return ColdStockOwners(
        LinkValue,
        StockValues,
        CutValue,
        FramesValue,
        Selected,
        AtomIds[Selected],
        StockAtoms,
        WrapperValue,
    )
