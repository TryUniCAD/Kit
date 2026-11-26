from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# system attachment must retain the same concrete folders and planes across configuration and resolved stream ownership
@DataClass(frozen=True, slots=True)
class SystemNodes:
    FolderValues: dict[str, ArchiveNode]
    CabinetValue: ArchiveNode
    PlaneValues: dict[str, ArchiveNode]
    FeatureValues: tuple[ArchiveNode, ...]
    RuntimeCaches: dict[str, ArchiveNode]
