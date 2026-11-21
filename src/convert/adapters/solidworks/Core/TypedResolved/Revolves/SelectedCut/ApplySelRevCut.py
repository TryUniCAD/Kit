from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockDesigns import (
    StockDesigns,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.WithCutSelection import (
    BindCutPick,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.BindRevDoc import (
    BindRevDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutCache import (
    RevCutCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutLineage import (
    RevCutLineage,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp


# the cut consumes one historical stock while leaving both final physical bodies independently owned
def ApplySelRevCut(
    DocumentValue: CadDocument,
    LinkValue: NativeLink,
    Lineage: RevCutLineage,
    CacheValue: RevCutCache,
) -> CadDocument:
    First, Second = Lineage.StockValues
    CutValue = Lineage.CutValue
    StockId = NativeNodeId(Lineage.SelectedValue.NodeValue)
    CutId = NativeNodeId(CutValue.NodeValue)
    StockKey = f"sldprt:feature:{StockId}"
    Result = BindRevDoc(
        DocumentValue, LinkValue, First, BooleanOp.KCreate, CheckFront=True
    )
    Result = BindRevDoc(Result, LinkValue, Second, BooleanOp.KCreate, CheckFront=True)
    Result = BindRevDoc(
        Result, LinkValue, CutValue, BooleanOp.KCutOperation, StockKey, CheckFront=True
    )
    Steps = {Value.id: Value for Value in Result.feature_timeline}
    Result = BindCutPick(Result, Steps[StockKey], Steps[f"sldprt:feature:{CutId}"])
    return ReplaceValue(
        Result,
        brep=CacheValue.BrepValue,
        bodies=StockDesigns(CacheValue, Result.feature_timeline, Result.brep_payloads),
        metadata=FreezeMapping(
            {
                **Result.metadata,
                "solidworks.typed_revolve_cut": {
                    "status": "projected_saved_selection",
                    "stock_feature_ids": tuple(
                        NativeNodeId(Value.NodeValue) for Value in Lineage.StockValues
                    ),
                    "selected_producer_id": StockId,
                    "consumer_feature_id": CutId,
                    "consumed_atom_id": Lineage.AtomsValue.ConsumedAtom.FieldsValue[
                        "f140"
                    ],
                    "untouched_atom_id": Lineage.AtomsValue.UntouchedAtom.FieldsValue[
                        "f140"
                    ],
                    "result_atom_id": Lineage.AtomsValue.ResultAtom.FieldsValue["f140"],
                    "selector_owner": NativeNodeSpan(LinkValue, Lineage.WrapperValue),
                    "public_writer_qualified": False,
                },
            }
        ),
    )
