from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the note head and end remain distinct nodes with actual reciprocal references
@DataClass(frozen=True, slots=True)
class NotesGraph:
    HeadValue: ArchiveNode
    EndValue: ArchiveNode
