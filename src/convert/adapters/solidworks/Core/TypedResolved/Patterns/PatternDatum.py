from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Patterns.TiltOwner import TiltOwner


# a selected plane supplies the direction and retains its angle history when present
@DataClass(frozen=True, slots=True)
class PatternDatum:
    PlaneValue: ArchiveNode
    LineValue: ArchiveNode
    FrameValue: PlaneFrame
    ReversedValue: bool
    TiltValue: TiltOwner
