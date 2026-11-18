from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossBase import (
    RequireBossBase,
)
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# only the complete ordinary forward blind create operation is proven by the first part construction profile
def RequireBossDef(FeatureValue: FeatureStep) -> ExtrudeFeature:
    Definition = RequireBossBase(FeatureValue)
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.reversed
        or Definition.symmetric
    ):
        raise ValueError("plain boss requires a single forward blind termination")
    if Definition.direction is not None and (
        Definition.direction.x,
        Definition.direction.y,
        Definition.direction.z,
    ) != (0.0, 0.0, 1.0):
        raise ValueError("plain boss requires the canonical forward plane normal")
    if (
        Definition.second_length is not None
        or Definition.second_end_condition is not None
    ):
        raise ValueError("plain boss does not admit a second direction")
    return Definition
