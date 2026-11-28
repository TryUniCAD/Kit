from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckCylTrim import (
    CheckCylTrim,
)
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CylRim import CylRim
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepTopology import BrepLoop


# a periodic side trim must reach the actual cap through the shared edge owner
def ReadCylRim(TopologyValue: BrepTopology, SideLoop: BrepLoop) -> CylRim:
    if len(SideLoop.coedge_ids) != 1:
        raise ValueError("local cylinder mantle loop requires one coedge")
    SideUse = TopologyValue.coedges[SideLoop.coedge_ids[0]]
    EdgeValue = TopologyValue.edges[SideUse.edge_id]
    CapUses = tuple(
        UseId
        for UseId in TopologyValue.edge_coedges[EdgeValue.id]
        if UseId != SideUse.id
    )
    if len(CapUses) != 1 or SideUse.reversed or SideUse.pcurve_id:
        raise ValueError("local cylinder mantle edge has an unqualified opposite use")
    CapUse = TopologyValue.coedges[CapUses[0]]
    CapLoop = TopologyValue.loops[TopologyValue.coedge_loop[CapUse.id]]
    CapFace = TopologyValue.faces[TopologyValue.loop_face[CapLoop.id]]
    PlaneValue = TopologyValue.surface_by_id[CapFace.surface_id]
    CircleValue = TopologyValue.curve_by_id[EdgeValue.curve_id]
    if (
        type(PlaneValue) is not PlaneSurface
        or type(CircleValue) is not CircleCurve
        or CapFace.loop_ids != (CapLoop.id,)
        or CapLoop.coedge_ids != (CapUse.id,)
        or not CapLoop.outer
        or not CapUse.reversed
        or CapUse.pcurve_id
    ):
        raise ValueError("local cylinder rim is missing its oriented cap or circle")
    CheckCylTrim(TopologyValue, EdgeValue, CircleValue)
    return CylRim(
        CapFace, CapLoop, CapUse, SideLoop, SideUse, EdgeValue, CircleValue, PlaneValue
    )
