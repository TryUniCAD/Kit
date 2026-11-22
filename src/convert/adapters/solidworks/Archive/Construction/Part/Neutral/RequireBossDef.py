from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# only the complete ordinary forward blind create operation is proven by the first part construction profile
def RequireBossDef(
    FeatureValue: FeatureStep, AxisValue: str = "z", IsReversed: bool = False
) -> ExtrudeFeature:
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
        or Definition.reversed != IsReversed
        or Definition.symmetric
    ):
        raise ValueError("plain boss requires a single forward blind termination")
    if (
        Definition.direction is not None
        and (
            Definition.direction.x,
            Definition.direction.y,
            Definition.direction.z,
        )
        != PrincipalFrame(AxisValue).NormalValue
    ):
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
