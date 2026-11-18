from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from interchange.Features.FeatureExtrude import ExtrudeEnd


# an extrusion supplement keeps its profile termination and every active length owner together
@DataClass(frozen=True, slots=True)
class ExtrudeOwner:
    NodeValue: ArchiveNode
    ProfileValue: ArchiveNode
    ParentsValue: tuple[ArchiveNode, ...]
    EndValue: ArchiveNode
    DepthValue: DepthOwner
    IsReversed: bool
    ModeValue: ExtrudeEnd
    SecondValue: DepthOwner | None = None
