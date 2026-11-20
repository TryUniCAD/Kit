from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.WithCutSelection import (
    BindCutPick,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp


# ordinary neutral builders must keep independent bosses and the consumed stock selection distinct
def BindStockDoc(DocValue: CadDocument, Lineage: StockCutLineage) -> CadDocument:
    StockIds = tuple(
        f"sldprt:feature:{NativeNodeId(OwnerValue.NodeValue)}"
        for OwnerValue in Lineage.StockValues
    )
    CutId = f"sldprt:feature:{NativeNodeId(Lineage.CutValue.NodeValue)}"
    StepValues = tuple(
        (
            ReplaceValue(Value, operation=BooleanOp.KCreate)
            if Value.id in StockIds
            else Value
        )
        for Value in DocValue.feature_timeline
    )
    Steps = {Value.id: Value for Value in StepValues}
    Stock = Steps[StockIds[Lineage.AtomsValue.SelectedIndex]]
    Bound = ReplaceValue(DocValue, feature_timeline=StepValues)
    return BindCutPick(Bound, Stock, Steps[CutId])
