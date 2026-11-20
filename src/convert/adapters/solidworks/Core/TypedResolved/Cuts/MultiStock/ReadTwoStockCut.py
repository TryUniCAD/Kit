from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import (
    CheckCutScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.CheckStockFace import (
    CheckStockFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtoms import (
    ReadStockAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
    ReadStockOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
    ReadStockRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
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
    AtomsValue = ReadStockAtoms(
        LinkValue, FirstStock.NodeValue, SecondStock.NodeValue, CutValue.NodeValue
    )
    StockValues = (FirstStock, SecondStock)
    Selected = StockValues[AtomsValue.SelectedIndex].NodeValue
    AtomId = ReadCutAtomId(AtomsValue.ConsumedAtom, Selected)
    CutNode = CutValue.NodeValue
    if CheckCutScope(RootValue, Selected, CutNode, AtomId, StockScope=0) != 1:
        raise ValueError("two stock cut requires its actual selected scope")
    Wrapper = ReadSingleNode(CutNode.FieldsValue.get("f548"), "moCompSolidBody_c")
    CheckStockFace(Wrapper, Selected)
    return StockCutLineage(
        StockValues, CutValue, AtomsValue, Wrapper, (FirstFrame, SecondFrame, CutFrame)
    )
