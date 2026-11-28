from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# named families need explicit admission identities while the frozen front profile keeps its original scope
@DataClass(frozen=True, slots=True)
class NamedGraph:
    DocumentValue: ArchiveNode
    VersionValue: int
    OrientationValue: str
