from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# assembly publication must retain actual model manager configuration feature and allocator identities throughout all linked streams
@DataClass(frozen=True, slots=True)
class AssemblyState:
    RootValue: ArchiveNode
    ManagerValue: ArchiveNode
    CurrentConfig: ArchiveNode
    FeatureValues: tuple[ArchiveNode, ...]
    PlaneValues: dict[str, ArchiveNode]
    GroupValue: ArchiveNode
    Allocator: PersistentIds
