from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# retained display references must keep native ownership before portable sketch resolution exists
@DataClass(frozen=True, slots=True)
class ProfileDisplay:
    DisplayValue: ArchiveNode
    FolderValue: ArchiveNode
    ViewValue: ArchiveNode
    ReferenceValue: ArchiveNode
    CanHideSuppressed: bool
