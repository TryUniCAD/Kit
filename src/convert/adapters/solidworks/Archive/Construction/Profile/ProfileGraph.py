from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipseGraph import (
    EllipseGraph,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# a generated profile retains its actual sketch reference and frame for downstream operation construction
@DataClass(frozen=True, slots=True)
class ProfileGraph:
    ProfileValue: ArchiveNode
    GeometryValue: PolygonGraph | CircleGraph | EllipseGraph
    ReferenceValue: ArchiveNode
    FrameValue: PlaneFrame
