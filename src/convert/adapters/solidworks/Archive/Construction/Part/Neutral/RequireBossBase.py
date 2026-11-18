from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# supported boss variants share their actual create operation ownership and simple through section profile state
def RequireBossBase(FeatureValue: FeatureStep) -> ExtrudeFeature:
    Definition = FeatureValue.definition
    if (
        FeatureValue.kind != FeatureKind.KExtrusion
        or type(Definition) is not ExtrudeFeature
        or FeatureValue.operation != BooleanOp.KCreate
    ):
        raise ValueError("ordinary boss requires an actual create extrusion definition")
    if (
        FeatureValue.suppressed
        or FeatureValue.configuration_states
        or FeatureValue.selection_ids
        or FeatureValue.input_feature_ids
        or FeatureValue.attributes
    ):
        raise ValueError(
            "ordinary boss does not admit suppressed configured selected dependent or extended feature state"
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
            "ordinary boss does not admit offset draft or target references"
        )
    return Definition
