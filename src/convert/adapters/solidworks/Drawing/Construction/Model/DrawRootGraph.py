from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetGraph import SheetGraph


# callers need the actual completed root sheet and allocator before constructing metadata or a complete native stream
@DataClass(frozen=True, slots=True)
class DrawRootGraph:
    ModelValue: ArchiveNode
    SheetValue: SheetGraph
    Allocator: PersistentIds
