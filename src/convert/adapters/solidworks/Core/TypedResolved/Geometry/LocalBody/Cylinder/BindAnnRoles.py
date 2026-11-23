from dataclasses import replace as Replace

from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# concentric planar trims must retain their geometric roles without reordering the wire
def BindAnnRoles(ModelValue: BrepModel) -> BrepModel:
    TopologyValue = BrepTopology(ModelValue)
    RolesValue: dict[str, bool] = {}
    for FaceValue in ModelValue.faces:
        if not isinstance(
            TopologyValue.surface_by_id[FaceValue.surface_id], PlaneSurface
        ):
            continue
        RadiiValue: dict[str, float] = {}
        for LoopId in FaceValue.loop_ids:
            (UseId,) = TopologyValue.loops[LoopId].coedge_ids
            EdgeValue = TopologyValue.edges[TopologyValue.coedges[UseId].edge_id]
            CurveValue = TopologyValue.curve_by_id[EdgeValue.curve_id]
            if not isinstance(CurveValue, CircleCurve):
                raise ValueError("local annulus cap requires circular rims")
            RadiiValue[LoopId] = CurveValue.radius
        Largest = max(RadiiValue.values())
        RolesValue.update(
            {LoopId: Radius == Largest for LoopId, Radius in RadiiValue.items()}
        )
    return Replace(
        ModelValue,
        loops=tuple(
            (
                Replace(Value, outer=RolesValue[Value.id])
                if Value.id in RolesValue
                else Value
            )
            for Value in ModelValue.loops
        ),
    )
