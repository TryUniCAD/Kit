from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrude,
)
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# a pocket consumes its actual earlier solid in the ordinary reversed blind direction
def RequireCutDef(FeatureValue: FeatureStep, PreviousId: str) -> ExtrudeFeature:
    Definition = RequireExtrude(FeatureValue, BooleanOp.KCutOperation, (PreviousId,))
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.reversed is not True
        or Definition.symmetric
        or Definition.second_length is not None
        or Definition.second_end_condition is not None
    ):
        raise ValueError("ordinary cut requires a single reversed blind termination")
    Direction = Definition.direction
    if Direction is not None and (Direction.x, Direction.y, Direction.z) != (
        0.0,
        0.0,
        1.0,
    ):
        raise ValueError("ordinary cut uses the canonical support normal")
    return Definition
