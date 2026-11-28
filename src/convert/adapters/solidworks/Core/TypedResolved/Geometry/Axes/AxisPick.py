from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a finite axis selection owns a distinct wrapper and component for one actual plane
@MakeDataClass(frozen=True, slots=True)
class AxisPick:
    PlaneValue: ArchiveNode
    WrapperValue: ArchiveNode
    ReferenceValue: ArchiveNode
    ComponentValue: ArchiveNode
    FrameValue: PlaneFrame
