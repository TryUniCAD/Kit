from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# linked streams need their own admission boundary instead of weakening the frozen blank profile
@DataClass(frozen=True, slots=True)
class FrontGraph:
    DocumentValue: ArchiveNode
    VersionValue: int
