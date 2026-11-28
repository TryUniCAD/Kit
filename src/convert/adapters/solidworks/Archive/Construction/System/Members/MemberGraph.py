from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.System.Members.NotesGraph import (
    NotesGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# generated member relationships expose actual nodes rather than substituted source identifier words
@DataClass(frozen=True, slots=True)
class MemberGraph:
    NotesValue: NotesGraph
    LightValues: tuple[ArchiveNode, ...]
