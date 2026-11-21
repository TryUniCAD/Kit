from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the native mate factory must share its actual parent ownership release and persistent allocator
@DataClass(frozen=True, slots=True)
class MateContext:
    AssemblyValue: ArchiveNode
    GroupValue: ArchiveNode
    HeaderValue: ArchiveNode
    ConfigValue: ArchiveNode
    TargetValue: FeatureTarget
    Allocator: PersistentIds
    PreviousValues: tuple[ArchiveNode, ...] = ()
