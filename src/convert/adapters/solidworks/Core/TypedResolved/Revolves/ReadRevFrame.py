from collections.abc import Mapping
from math import hypot as Hypot

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.RevolveProfile import (
    RevolveProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAxis import (
    RevolveAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.MapRevPoint import (
    MapRevPoint,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


# independent native reversal changes sweep sense without changing the selected sketch line or positive angle
def ReadRevFrame(
    ProfileValue: ArchiveNode,
    RootValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    GraphValue: RevolveProfile,
    IsReverse: bool,
) -> RevolveAxis:
    FrameValue = ReadPrismFrame(ProfileValue, RootValue, Features)
    StartValue = MapRevPoint(
        FrameValue, GraphValue.AxisPoints[GraphValue.AxisValue.StartValue].PositionValue
    )
    EndValue = MapRevPoint(
        FrameValue, GraphValue.AxisPoints[GraphValue.AxisValue.EndValue].PositionValue
    )
    DeltaValue = (
        EndValue.x - StartValue.x,
        EndValue.y - StartValue.y,
        EndValue.z - StartValue.z,
    )
    LengthValue = Hypot(*DeltaValue)
    if LengthValue < 1e-5:
        raise ValueError("ordinary revolve axis falls below native endpoint tolerance")
    RawValue = SpaceVector(*(Value / LengthValue for Value in DeltaValue))
    Multiplier = -1.0 if IsReverse else 1.0
    return RevolveAxis(
        StartValue,
        EndValue,
        SpaceVector(
            RawValue.x * Multiplier, RawValue.y * Multiplier, RawValue.z * Multiplier
        ),
        RawValue,
    )
