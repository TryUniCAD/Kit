from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.WithColdCut import (
    WithColdCut,
)
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
def BindStockDoc(
    DocValue: CadDocument, Lineage: StockCutLineage | ColdStockOwners | None
) -> CadDocument:
    if Lineage is None:
        return DocValue
    StockIds = tuple(
        f"sldprt:feature:{NativeNodeId(OwnerValue.NodeValue)}"
        for OwnerValue in Lineage.StockValues
    )
    CutId = f"sldprt:feature:{NativeNodeId(Lineage.CutValue.NodeValue)}"
    StepValues = tuple(
        (
            ReplaceValue(Value, operation=BooleanOp.KCreate)
            if Value.id in StockIds
            else (
                WithColdCut(Value, Lineage.ProfileFrames[2].z_axis)
                if Value.id == CutId and isinstance(Lineage, ColdStockOwners)
                else Value
            )
        )
        for Value in DocValue.feature_timeline
    )
    Steps = {Value.id: Value for Value in StepValues}
    SelectedIndex = (
        Lineage.SelectedIndex
        if isinstance(Lineage, ColdStockOwners)
        else Lineage.AtomsValue.SelectedIndex
    )
    Stock = Steps[StockIds[SelectedIndex]]
    Bound = ReplaceValue(DocValue, feature_timeline=StepValues)
    return BindCutPick(Bound, Stock, Steps[CutId])
