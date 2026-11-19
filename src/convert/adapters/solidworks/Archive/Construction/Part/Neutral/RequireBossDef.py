from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrusion,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# a blind create operation must retain the expected reversal and actual support normal
def RequireBossDef(
    FeatureValue: FeatureStep, AxisValue: str = "z", IsReversed: bool = False
) -> ExtrudeFeature:
    Definition = RequireExtrusion(FeatureValue)
    if (
        Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.reversed != IsReversed
        or Definition.symmetric
    ):
        raise ValueError("plain boss requires its admitted single blind direction")
    if (
        Definition.direction is not None
        and (
            Definition.direction.x,
            Definition.direction.y,
            Definition.direction.z,
        )
        != PrincipalFrame(AxisValue).NormalValue
    ):
        raise ValueError("plain boss requires its actual principal plane normal")
    if (
        Definition.second_length is not None
        or Definition.second_end_condition is not None
    ):
        raise ValueError("plain boss does not admit a second direction")
    return Definition
