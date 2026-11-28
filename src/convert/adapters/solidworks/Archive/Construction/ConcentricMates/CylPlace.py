from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# both active and detached wrappers need exactly the same derived carrier at one actual occurrence
@DataClass(frozen=True, slots=True)
class CylPlace:
    Occurrence: ArchiveNode
    FrameValue: PlaneFrame
    LocalAxis: tuple[float, float, float]
    OriginValue: tuple[float, float, float]
    WorldAxis: tuple[float, float, float]
