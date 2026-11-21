from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native detailing identities must remain distinct from drawing feature identifiers
@DataClass(frozen=True, slots=True)
class DetailEntry:
    ComponentKey: str
    DownstreamId: int
    RefValue: ArchiveNode
