from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetInput import SheetInput
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames


# native creation time provenance and allocator state require explicit caller ownership
@DataClass(frozen=True, slots=True)
class SheetBuild:
    InputValue: SheetInput
    NamesValue: SheetNames
    FirstIdValue: int
    CreatedAtValue: int
    DateCodeValue: int
    KernelVersion: int
    ArchiveVersion: int
    ServicePack: int
    SubservicePack: int
