from math import tau as FullTurn

from convert.Geometry.Parasolid import BrepTopology
from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CheckCylTrim import (
    CheckCylTrim,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    PrismVector,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)


# a periodic edge must actually pair a cap trim with a wall trim
def RingUse(
    TopologyValue: BrepTopology, UseId: str
) -> tuple[BrepCoedge, BrepLoop, BrepFace]:
    UseValue = TopologyValue.coedges[UseId]
    LoopValue = TopologyValue.loops[TopologyValue.coedge_loop[UseId]]
    FaceValue = TopologyValue.faces[TopologyValue.loop_face[LoopValue.id]]
    if UseValue.pcurve_id or LoopValue.coedge_ids != (UseId,):
        raise ValueError("local annulus requires one closed use on each rim loop")
    return UseValue, LoopValue, FaceValue


# a radius and cap orientation must agree with the actual circular edge incidence
def CheckAnnEdge(
    TopologyValue: BrepTopology,
    EdgeValue: BrepEdge,
    OuterWall: CylinderSurface,
    AllowInset: bool,
) -> tuple[tuple[str, str], CircleCurve]:
    First, Second = (
        RingUse(TopologyValue, UseId)
        for UseId in TopologyValue.edge_coedges[EdgeValue.id]
    )
    if isinstance(TopologyValue.surface_by_id[First[2].surface_id], CylinderSurface):
        First, Second = Second, First
    CapUse, CapLoop, CapFace = First
    SideUse, _, SideFace = Second
    PlaneValue = TopologyValue.surface_by_id[CapFace.surface_id]
    WallValue = TopologyValue.surface_by_id[SideFace.surface_id]
    CircleValue = TopologyValue.curve_by_id[EdgeValue.curve_id]
    if (
        type(PlaneValue) is not PlaneSurface
        or type(WallValue) is not CylinderSurface
        or type(CircleValue) is not CircleCurve
    ):
        raise ValueError(
            "local annulus rim must pair an actual cap and cylindrical wall"
        )
    Outside = WallValue is OuterWall
    NormalParts = PrismVector(PlaneValue.normal)
    CircleParts = PrismVector(CircleValue.axis)
    CircleAxes = (NormalParts, tuple(-Value for Value in NormalParts))
    FollowsNormal = (CircleParts == NormalParts) == CapFace.same_sense
    if (
        CircleValue.radius != WallValue.radius
        or (Outside or not AllowInset)
        and CircleValue.center != PlaneValue.origin
        or CircleParts not in CircleAxes
        or CapUse.reversed == SideUse.reversed
        or CapLoop.outer != Outside
        or CapUse.reversed != (Outside != FollowsNormal)
    ):
        raise ValueError("local annulus has inconsistent signed cap or rim geometry")
    CheckSweepFrame(
        CircleValue.center, CircleValue.axis, CircleValue.reference_direction
    )
    return (PlaneValue.id, WallValue.id), CircleValue


# each cap must meet every wall through a distinct completely owned rim
def CheckAnnEdges(
    ModelValue: BrepModel,
    TopologyValue: BrepTopology,
    OuterWall: CylinderSurface,
    WallCount: int,
    *,
    CheckSeams: bool,
) -> dict[tuple[str, str], CircleCurve]:
    PairsValue: dict[tuple[str, str], CircleCurve] = {}
    for EdgeValue in ModelValue.edges:
        if (
            EdgeValue.start_vertex_id != EdgeValue.end_vertex_id
            or (EdgeValue.start_parameter, EdgeValue.end_parameter) != (0.0, FullTurn)
            or EdgeValue.degenerate
            or len(TopologyValue.edge_coedges[EdgeValue.id]) != 2
        ):
            raise ValueError("local annulus requires one full circle trim per edge")
        CurveValue = TopologyValue.curve_by_id[EdgeValue.curve_id]
        if not isinstance(CurveValue, CircleCurve):
            raise ValueError("local annulus rim requires a circular carrier")
        if CheckSeams:
            CheckCylTrim(TopologyValue, EdgeValue, CurveValue)
        PairValue, RingValue = CheckAnnEdge(
            TopologyValue, EdgeValue, OuterWall, WallCount > 2
        )
        PairsValue[PairValue] = RingValue
    if len(PairsValue) != 2 * WallCount:
        raise ValueError("local annulus rims do not join both caps to all walls")
    return PairsValue
