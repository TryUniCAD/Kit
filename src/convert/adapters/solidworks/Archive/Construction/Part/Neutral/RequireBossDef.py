from typing import cast as CastValue

from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# blind preparation must retain explicit direction while publication separately requires exact native measurement
def RequireBossDef(FeatureValue: FeatureStep) -> ExtrudeFeature:
    Definition = FeatureValue.definition
    if (
        FeatureValue.kind != FeatureKind.KExtrusion
        or type(Definition) is not ExtrudeFeature
        or FeatureValue.operation != BooleanOp.KCreate
    ):
        raise ValueError("plain boss requires an actual create extrusion definition")
    if (
        FeatureValue.suppressed
        or FeatureValue.configuration_states
        or FeatureValue.selection_ids
        or FeatureValue.input_feature_ids
        or FeatureValue.attributes
    ):
        raise ValueError(
            "plain boss does not admit suppressed configured selected dependent or extended feature state"
        )
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or type(CastValue(object, Definition.reversed)) is not bool
        or Definition.symmetric
    ):
        raise ValueError(
            "plain boss requires a single blind termination and boolean direction"
        )
    if Definition.direction is not None and (
        Definition.direction.x,
        Definition.direction.y,
        Definition.direction.z,
    ) != (0.0, 0.0, 1.0):
        raise ValueError("plain boss requires the canonical forward plane normal")
    if (
        any(
            ValueInput is not None
            for ValueInput in (
                Definition.second_length,
                Definition.second_end_condition,
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
            "plain boss does not admit second direction offset draft or target reference semantics"
        )
    return Definition
