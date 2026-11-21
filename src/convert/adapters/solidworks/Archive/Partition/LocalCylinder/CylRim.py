from dataclasses import dataclass as DataClass

from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)


# a closed rim carries the actual paired uses and their shared authored geometry
@DataClass(frozen=True, slots=True)
class CylRim:
    CapFace: BrepFace
    CapLoop: BrepLoop
    CapUse: BrepCoedge
    SideLoop: BrepLoop
    SideUse: BrepCoedge
    EdgeValue: BrepEdge
    CircleValue: CircleCurve
    PlaneValue: PlaneSurface
