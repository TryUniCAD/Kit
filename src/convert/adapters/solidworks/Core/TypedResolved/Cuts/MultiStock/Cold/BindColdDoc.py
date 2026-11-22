from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockPart import (
    ColdStockPart,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.Selection import Selection, SelectPathElem


# a stock result retains the consumed producer as an explicit historical body selection
def BindColdDoc(DocumentValue: CadDocument, PartValue: ColdStockPart) -> CadDocument:
    Owners = PartValue.OwnersValue
    StockIds = tuple(
        f"sldprt:feature:{NativeNodeId(Owner.NodeValue)}"
        for Owner in Owners.StockValues
    )
    CutId = f"sldprt:feature:{NativeNodeId(Owners.CutValue.NodeValue)}"
    Steps = {StepValue.id: StepValue for StepValue in DocumentValue.feature_timeline}
    Selected = Steps[StockIds[Owners.SelectedIndex]]
    CutStep = Steps[CutId]
    if (
        Selected.id not in CutStep.input_feature_ids
        or not isinstance(CutStep.definition, ExtrudeFeature)
        or CutStep.definition.direction != Owners.ProfileFrames[2].z_axis
        or CutStep.selection_ids
        or DocumentValue.selections
    ):
        raise ValueError("neutral cut lacks the actual signed selected operation")
    Selector = Selection(
        CutStep.id + ":stock-body",
        Selected.name + " body",
        (SelectPathElem("feature", Selected.id, "body"),),
        provenance=TypedProvenance(
            NativeNodeSpan(Owners.LinkValue, Owners.WrapperValue), CutStep.id
        ),
    )
    return ReplaceValue(
        DocumentValue,
        bodies=PartValue.BodiesValue,
        selections=(Selector,),
        feature_timeline=tuple(
            (
                ReplaceValue(StepValue, operation=BooleanOp.KCreate)
                if StepValue.id in StockIds
                else (
                    ReplaceValue(StepValue, selection_ids=(Selector.id,))
                    if StepValue is CutStep
                    else StepValue
                )
            )
            for StepValue in DocumentValue.feature_timeline
        ),
    )
