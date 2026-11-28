from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# cold names need actual graph owners while computed geometry retains its separate neutral identity
@DataClass(frozen=True, slots=True)
class ColdOutput:
    LinkValue: NativeLink
    AtomValue: ArchiveNode
    BossValue: ArchiveNode
    NameValue: str
