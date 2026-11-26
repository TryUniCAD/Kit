from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemNodes import (
    SystemNodes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the complete fresh system subgraph exposes distinct manager and resolved roots without inventing an encoded part manager alias
@DataClass(frozen=True, slots=True)
class PartSystem:
    RootValue: ArchiveNode
    ManagerValue: ArchiveNode
    ConfigValues: tuple[ArchiveNode, ...]
    SystemValues: SystemNodes
    OriginValue: OriginGraph
    FeatureValues: tuple[ArchiveNode, ...]
