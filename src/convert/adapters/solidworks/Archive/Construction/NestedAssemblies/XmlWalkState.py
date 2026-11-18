from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# generated document indexes need an independent xml id namespace with shared definitions and direct per model reference rows
@DataClass(slots=True)
class XmlWalkState:
    NodeIds: dict[int, tuple[int, int]]
    FileValues: list[TargetDocument]
    ModelValues: list[TargetDocument]
    RefValues: dict[int, list[tuple[int, ArchiveNode, int]]]
    NextValue: int
