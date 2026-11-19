from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.Transform import Transform


# the first cold circle route retains the two native qualified public writer profiles instead of accepting every finite analytic cylinder
def CheckCircMode(
    OwnerValue: ExtrudeOwner, CircleValue: LocalCircle, FrameValue: Transform
) -> None:
    Normal = FrameValue.z_axis
    ProfileValue = (
        (Normal.x, Normal.y, Normal.z),
        CircleValue.ModeValue,
        OwnerValue.IsReversed,
    )
    if (
        OwnerValue.ModeValue != ExtrudeEnd.KBlind
        or OwnerValue.SecondValue is not None
        or ProfileValue
        not in {((0.0, 0.0, 1.0), "diameter", False), ((0.0, 1.0, 0.0), "radius", True)}
    ):
        raise ValueError(
            "cache free circle is outside the qualified support driver and direction profiles"
        )
