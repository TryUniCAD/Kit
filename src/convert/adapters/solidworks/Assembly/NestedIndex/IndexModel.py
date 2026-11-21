from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the selected model keeps its actual configuration root and full header key for cross-file occurrence checks
@DataClass(frozen=True, slots=True)
class IndexModel:
    RootValue: ArchiveNode
    KeyValue: tuple[str, str, int, int]
    NameValue: str
