from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateSelection import (
    MateSelection,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native mate inputs separate authored relationship and provenance from generated graph bookkeeping
@DataClass(frozen=True, slots=True)
class PlanarMateIn:
    KindValue: str
    NameValue: str
    Selections: tuple[MateSelection, MateSelection]
    FixedValue: ArchiveNode
    CreatedValue: int
