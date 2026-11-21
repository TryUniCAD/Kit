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
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveEnd import (
    RevolveEnd,
)


# complete feature ownership binds its live parameter selected axis and independent body contour atomically
@Dataclass(frozen=True, slots=True)
class RevolveOwner:
    NodeValue: ArchiveNode
    ProfileValue: ArchiveNode
    SketchValue: ArchiveNode
    EndValue: RevolveEnd
    AxisValue: AxisReference
    ProfileGraph: RevolveProfile
    FrameValue: RevolveAxis
    IsReverse: bool

    # existing primary angle consumers keep the actual forward display owner
    @property
    def AngleValue(self) -> RevolveAngle:
        return self.EndValue.AlongValue
