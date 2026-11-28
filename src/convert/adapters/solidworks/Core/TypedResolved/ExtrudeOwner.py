from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from interchange.Features.FeatureExtrude import ExtrudeEnd


# an extrusion supplement needs one coherent profile dependency end specification and live depth owner
@DataClass(frozen=True, slots=True)
class ExtrudeOwner:
    NodeValue: ArchiveNode
    ProfileValue: ArchiveNode
    ParentsValue: tuple[ArchiveNode, ...]
    EndValue: ArchiveNode
    DepthValue: DepthOwner | None
    IsReversed: bool
    ModeValue: ExtrudeEnd = ExtrudeEnd.KBlind

    # a finite stock extent requires its live depth owner
    def RequireDepth(self) -> DepthOwner:
        if self.DepthValue is None:
            raise ValueError("finite extrusion requires an active native depth owner")
        return self.DepthValue
