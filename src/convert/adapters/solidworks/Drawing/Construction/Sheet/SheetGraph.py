from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# callers need actual support identities and allocator progress when composing the remaining drawing
@DataClass(frozen=True, slots=True)
class SheetGraph:
    SheetValue: ArchiveNode
    PlaneValue: ArchiveNode
    ProfileValue: ArchiveNode
    DetailValue: ArchiveNode
    UiSketch: ArchiveNode
    NextIdValue: int
