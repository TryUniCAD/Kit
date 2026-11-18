from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# the extrusion definition must retain its actual operation and ordered dependencies
def RequireExtrusion(
    FeatureValue: FeatureStep,
    OperationValue: BooleanOp = BooleanOp.KCreate,
    PreviousIds: tuple[str, ...] = (),
    *,
    ExpectedSelections: tuple[str, ...] = (),
) -> ExtrudeFeature:
    Definition = FeatureValue.definition
    if (
        FeatureValue.kind != FeatureKind.KExtrusion
        or type(Definition) is not ExtrudeFeature
        or FeatureValue.operation != OperationValue
    ):
        raise ValueError("ordinary extrusion requires its actual operation definition")
    if (
        FeatureValue.suppressed
        or FeatureValue.configuration_states
        or FeatureValue.selection_ids != ExpectedSelections
        or FeatureValue.input_feature_ids != PreviousIds
        or FeatureValue.attributes
    ):
        raise ValueError(
            "ordinary extrusion requires active unextended features with the admitted dependency order"
        )
    if (
        any(
            ValueInput is not None
            for ValueInput in (
                Definition.offset,
                Definition.second_offset,
                Definition.draft_angle,
                Definition.second_draft_angle,
            )
        )
        or Definition.up_to_reference
        or Definition.second_up_to_reference
    ):
        raise ValueError(
            "ordinary extrusion requires its simple start and end definitions"
        )
    return Definition
