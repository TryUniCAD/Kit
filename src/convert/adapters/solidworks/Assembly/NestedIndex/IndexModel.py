from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the selected model keeps its root and complete header key for checking occurrence identity across files
@DataClass(frozen=True, slots=True)
class IndexModel:
    RootValue: ArchiveNode
    KeyValue: tuple[str, str, int, int]
    NameValue: str
