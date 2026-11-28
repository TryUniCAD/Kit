from math import tau as FullTurn

from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# a complete periodic solid must retain both full circles and their derived seam vertices
def CheckCylBrep(ModelValue: BrepModel) -> None:
    if (
        len(ModelValue.bodies) != 1
        or len(ModelValue.regions) != 1
        or not ModelValue.regions[0].solid
        or len(ModelValue.shells) != 1
        or not ModelValue.shells[0].closed
        or len(ModelValue.faces) != 3
        or len(ModelValue.surfaces) != 3
        or sum(isinstance(Surface, PlaneSurface) for Surface in ModelValue.surfaces)
        != 2
        or sum(isinstance(Surface, CylinderSurface) for Surface in ModelValue.surfaces)
        != 1
        or len(ModelValue.loops) != 4
        or any(len(LoopValue.coedge_ids) != 1 for LoopValue in ModelValue.loops)
        or len(ModelValue.coedges) != 4
        or len(ModelValue.edges) != 2
        or len(ModelValue.vertices) != 2
        or len(ModelValue.curves) != 2
        or not all(
            isinstance(CurveValue, CircleCurve) for CurveValue in ModelValue.curves
        )
        or any(
            EdgeValue.start_vertex_id != EdgeValue.end_vertex_id
            or (EdgeValue.start_parameter, EdgeValue.end_parameter) != (0.0, FullTurn)
            or EdgeValue.degenerate
            for EdgeValue in ModelValue.edges
        )
        or {EdgeValue.start_vertex_id for EdgeValue in ModelValue.edges}
        != {VertexValue.id for VertexValue in ModelValue.vertices}
        or ModelValue.validate()
    ):
        raise ValueError("local cylinder did not restore one complete periodic solid")
