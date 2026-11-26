from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a standalone model definition owns ui settings and its target archive version
@DataClass(frozen=True, slots=True)
class ModelDefGraph:
    DocumentValue: ArchiveNode
    VersionValue: int
