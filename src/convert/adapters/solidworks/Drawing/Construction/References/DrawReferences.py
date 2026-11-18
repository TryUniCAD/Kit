from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# both view and component properties must retain the same generated directory entry and their actual separate reference nodes
@DataClass(frozen=True, slots=True)
class DrawReferences:
    EntryValue: ArchiveNode
    InternalValue: ArchiveNode
    PropertyValue: ArchiveNode
