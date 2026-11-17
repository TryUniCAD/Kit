from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a complete definition needs a distinct ui owner around the model graph rather than a stream fragment
@DataClass(frozen=True, slots=True)
class BlankGraph:
    DocumentValue: ArchiveNode
    VersionValue: int
