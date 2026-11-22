from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.Selection import SelectPathElem


# portable json preserves a through end only when its signed cutter and selected solid are explicit
def JsonThroughCut(DocumentValue: CadDocument) -> str | None:
    Candidates = tuple(
        (StepValue, Definition)
        for StepValue in DocumentValue.feature_timeline
        if type(Definition := StepValue.definition) is ExtrudeFeature
        and Definition.length is None
    )
    if len(Candidates) != 1 or DocumentValue.assembly is not None:
        return None
    ((CutValue, Definition),) = Candidates
    if (
        CutValue.operation != BooleanOp.KCutOperation
        or Definition.end_condition != ExtrudeEnd.KThroughAll
        or Definition.direction is None
        or Definition.second_end_condition is not None
        or Definition.second_length is not None
        or len(CutValue.selection_ids) != 1
        or not any(
            SketchValue.id == CutValue.sketch_id
            and SketchValue.closed_profile_entity_ids
            for SketchValue in DocumentValue.sketches
        )
    ):
        return None
    (SelectionId,) = CutValue.selection_ids
    SelectionValue = next(
        (Value for Value in DocumentValue.selections if Value.id == SelectionId),
        None,
    )
    Producers = tuple(
        StepValue.id
        for StepValue in DocumentValue.feature_timeline
        if StepValue.id in CutValue.input_feature_ids
        and StepValue.order < CutValue.order
        and StepValue.operation in (BooleanOp.KCreate, BooleanOp.KJoin)
    )
    if (
        SelectionValue is None
        or len(Producers) != 1
        or SelectionValue.path != (SelectPathElem("feature", Producers[0], "body"),)
    ):
        return None
    return CutValue.id
