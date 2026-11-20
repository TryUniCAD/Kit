from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.Selection import Selection, SelectPathElem


# the portable cut should reference its actual selected stock producer without inheriting a native atom number
def BindCutStock(DocumentValue: CadDocument) -> CadDocument:
    Report = DocumentValue.metadata.get("solidworks.typed_resolved_semantics")
    Evidence = (
        Report.get("cut_body_dependency") if isinstance(Report, Mapping) else None
    )
    if not isinstance(Evidence, Mapping) or Evidence.get("feature_scope_code") != 1:
        return DocumentValue
    Producer = Evidence.get("producer_feature_id")
    Consumer = Evidence.get("consumer_feature_id")
    if type(Producer) is not int or type(Consumer) is not int:
        return DocumentValue
    Steps = {StepValue.id: StepValue for StepValue in DocumentValue.feature_timeline}
    Stock = Steps.get(f"sldprt:feature:{Producer}")
    CutStep = Steps.get(f"sldprt:feature:{Consumer}")
    if (
        Stock is None
        or CutStep is None
        or Stock.id not in CutStep.input_feature_ids
        or CutStep.operation != BooleanOp.KCutOperation
        or not isinstance(CutStep.definition, ExtrudeFeature)
        or CutStep.definition.end_condition != ExtrudeEnd.KThroughAll
        or len(DocumentValue.bodies) != 1
        or DocumentValue.bodies[0].final_feature_id != CutStep.id
    ):
        return DocumentValue
    Reference = Selection(
        CutStep.id + ":stock-body",
        Stock.name + " body",
        (SelectPathElem("feature", Stock.id, "body"),),
    )
    if any(Value.id == Reference.id for Value in DocumentValue.selections):
        raise ValueError("selected stock identity conflicts with an existing selection")
    BoundCut = ReplaceValue(
        CutStep, selection_ids=(*CutStep.selection_ids, Reference.id)
    )
    return ReplaceValue(
        DocumentValue,
        feature_timeline=tuple(
            BoundCut if Value is CutStep else Value
            for Value in DocumentValue.feature_timeline
        ),
        selections=(*DocumentValue.selections, Reference),
    )
