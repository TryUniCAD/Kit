from convert.adapters.solidworks.Archive.Construction.Circles.CircleModes import (
    KMeasCircModes,
    KOrdCircModes,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.Transform import Transform


# signed circle intervals require the actual principal basis and independent active directions
def CheckCircMode(
    OwnerValue: ExtrudeOwner, CircleValue: LocalCircle, FrameValue: Transform
) -> None:
    Normal = FrameValue.z_axis
    AxisValue = {(1.0, 0.0, 0.0): "x", (0.0, 1.0, 0.0): "y", (0.0, 0.0, 1.0): "z"}.get(
        (Normal.x, Normal.y, Normal.z)
    )
    ModeValue = (
        "two_directions"
        if OwnerValue.ModeValue is ExtrudeEnd.KTwoLengths
        else OwnerValue.ModeValue.value
    )
    ProfileValue = (
        AxisValue,
        CircleValue.ModeValue == "diameter",
        OwnerValue.IsReversed,
        ModeValue,
        OwnerValue.SecondValue is not None,
    )
    if CircleValue.ModeValue not in ("diameter", "radius") or (
        ProfileValue not in KMeasCircModes
    ):
        raise ValueError(
            "cache free circle is outside the qualified support driver and direction profiles"
        )
    if OwnerValue.ModeValue != ExtrudeEnd.KBlind or ProfileValue not in KOrdCircModes:
        _ = ReadPrincAxis(FrameValue)
