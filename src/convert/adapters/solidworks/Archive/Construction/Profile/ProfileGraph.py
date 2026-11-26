from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a generated profile must retain its actual polygon reference and frame for downstream operation construction without decoded saved state
@DataClass(frozen=True, slots=True)
class ProfileGraph:
    ProfileValue: ArchiveNode
    GeometryValue: PolygonGraph
    ReferenceValue: ArchiveNode
    FrameValue: PlaneFrame
