from convert.adapters.solidworks.Core.TypedResolved.Cuts.WithCutSelection import (
    BindCutPick,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevDoc import (
    BindRevDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp


# both saved and cold projections bind the live angular drivers and the historical body with the same selection semantics
def BindSelRevCut(
    Document: CadDocument,
    LinkValue: NativeLink,
    Stocks: tuple[RevolveOwner, RevolveOwner],
    Cutter: RevolveOwner,
    SelectedIndex: int,
) -> CadDocument:
    First, Second = Stocks
    StockKey = f"sldprt:feature:{NativeNodeId(Stocks[SelectedIndex].NodeValue)}"
    CutKey = f"sldprt:feature:{NativeNodeId(Cutter.NodeValue)}"
    Result = BindRevDoc(Document, LinkValue, First, BooleanOp.KCreate, CheckFront=True)
    Result = BindRevDoc(Result, LinkValue, Second, BooleanOp.KCreate, CheckFront=True)
    Result = BindRevDoc(
        Result, LinkValue, Cutter, BooleanOp.KCutOperation, StockKey, CheckFront=True
    )
    Steps = {Value.id: Value for Value in Result.feature_timeline}
    return BindCutPick(Result, Steps[StockKey], Steps[CutKey])
