from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# restored topology must stay bound to its actual archive marks and feature owners
@DataClass(frozen=True, slots=True)
class FilletOwners:
    StockValue: ArchiveNode
    FilletValue: ArchiveNode
    AtomValue: ArchiveNode
    Controllers: tuple[ArchiveNode, ArchiveNode, ArchiveNode]
