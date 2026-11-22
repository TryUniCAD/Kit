from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner


# an extrusion supplement needs one coherent profile dependency end specification and live depth owner
@DataClass(frozen=True, slots=True)
class ExtrudeOwner:
    NodeValue: ArchiveNode
    ProfileValue: ArchiveNode
    ParentsValue: tuple[ArchiveNode, ...]
    EndValue: ArchiveNode
    DepthValue: DepthOwner
    IsReversed: bool
