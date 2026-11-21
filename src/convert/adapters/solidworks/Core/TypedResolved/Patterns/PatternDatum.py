from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a selected plane supplies the direction without interpreting the line point
@DataClass(frozen=True, slots=True)
class PatternDatum:
    PlaneValue: ArchiveNode
    LineValue: ArchiveNode
    FrameValue: PlaneFrame
    ReversedValue: bool
