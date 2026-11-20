from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.Transform import Transform


# signed circle intervals require a measured combination of support driver direction and active ends
def CheckCircMode(
    OwnerValue: ExtrudeOwner, CircleValue: LocalCircle, FrameValue: Transform
) -> None:
    Normal = FrameValue.z_axis
    ProfileValue = (
        (Normal.x, Normal.y, Normal.z),
        CircleValue.ModeValue,
        OwnerValue.IsReversed,
        OwnerValue.ModeValue,
        OwnerValue.SecondValue is not None,
    )
    if ProfileValue not in {
        ((0.0, 0.0, 1.0), "diameter", False, ExtrudeEnd.KBlind, False),
        ((0.0, 1.0, 0.0), "radius", True, ExtrudeEnd.KBlind, False),
        ((1.0, 0.0, 0.0), "diameter", False, ExtrudeEnd.KMidPlane, False),
        ((0.0, 1.0, 0.0), "diameter", True, ExtrudeEnd.KTwoLengths, True),
    }:
        raise ValueError(
            "cache free circle is outside the qualified support driver and direction profiles"
        )
    if OwnerValue.ModeValue != ExtrudeEnd.KBlind:
        _ = ReadPrincAxis(FrameValue)
