from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Revolves.AxisReference import (
    AxisReference,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Profile.RevolveProfile import (
    RevolveProfile,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAxis import (
    RevolveAxis,
)


# complete feature ownership binds its live parameter selected axis and independent body contour atomically
@Dataclass(frozen=True, slots=True)
class RevolveOwner:
    NodeValue: ArchiveNode
    ProfileValue: ArchiveNode
    SketchValue: ArchiveNode
    AngleValue: RevolveAngle
    AxisValue: AxisReference
    ProfileGraph: RevolveProfile
    FrameValue: RevolveAxis
    IsReverse: bool
