from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateChild import (
    MateChild,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# authored mate selections retain actual occurrence and datum identities rather than names or byte locations
@DataClass(frozen=True, slots=True)
class MateSelection:
    OccurrenceValue: ArchiveNode
    ChildValue: MateChild
    DatumValue: ArchiveNode
