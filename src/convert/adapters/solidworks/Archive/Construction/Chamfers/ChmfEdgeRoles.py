from math import dist as Distance, isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import (
    ChmfEdgePlan,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import (
    ChmfEndpoints,
    ChmfFaceRole,
    ChmfStockGeom,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepCoedge

# two incident and two endpoint owners retain the selected fin traversal order
KChmfSupports = tuple[ChmfFaceRole, ChmfFaceRole, ChmfFaceRole, ChmfFaceRole]


# a topology edge must match both independently selected finite endpoints
def IsChmfEnds(
    Actual: tuple[KDatumVector, KDatumVector],
    Expected: tuple[KDatumVector, KDatumVector],
) -> bool:
    return any(
        all(
            Distance(First, Second) <= 1e-12
            for First, Second in zip(OrderValue, Expected, strict=True)
        )
        for OrderValue in (Actual, Actual[::-1])
    )


# select the stock edge from derived geometry instead of using a transient kernel index
def FindStockEdge(BodyValue: BrepModel, PickValue: ChmfEdgePlan) -> str:
    Endpoints = ChmfEndpoints(PickValue)
    Vertices = {
        Vertex.id: (
            Vertex.point.x * 0.001,
            Vertex.point.y * 0.001,
            Vertex.point.z * 0.001,
        )
        for Vertex in BodyValue.vertices
    }
    Edges = [
        EdgeValue.id
        for EdgeValue in BodyValue.edges
        if IsChmfEnds(
            (Vertices[EdgeValue.start_vertex_id], Vertices[EdgeValue.end_vertex_id]),
            Endpoints,
        )
    ]
    if len(Edges) != 1:
        raise ValueError("chamfer pick must resolve one actual predecessor edge")
    return Edges[0]


# coedge uses must pair opposite signs in the same closed stock boundary
def ChmfFinLinks(
    BodyValue: BrepModel,
) -> tuple[dict[str, list[BrepCoedge]], dict[str, str]]:
    EdgeUses: dict[str, list[BrepCoedge]] = {}
    for Coedge in BodyValue.coedges:
        EdgeUses.setdefault(Coedge.edge_id, []).append(Coedge)
    Opposites: dict[str, str] = {}
    for FinUses in EdgeUses.values():
        if len(FinUses) != 2 or FinUses[0].reversed == FinUses[1].reversed:
            raise ValueError(
                "chamfer requires exactly two reciprocal signed fins per stock edge"
            )
        First, Other = FinUses
        Opposites[First.id], Opposites[Other.id] = Other.id, First.id
    return EdgeUses, Opposites


# each real fin retains its unique incident loop and actual planar carrier
def ChmfLoopOwners(
    BodyValue: BrepModel,
) -> tuple[dict[str, tuple[str, tuple[str, ...]]], dict[str, PlaneSurface]]:
    Loops = {LoopValue.id: LoopValue.coedge_ids for LoopValue in BodyValue.loops}
    Surfaces = {Surface.id: Surface for Surface in BodyValue.surfaces}
    FinUses: dict[str, tuple[str, tuple[str, ...]]] = {}
    Carriers: dict[str, PlaneSurface] = {}
    for FaceValue in BodyValue.faces:
        (LoopId,) = FaceValue.loop_ids
        Surface = Surfaces[FaceValue.surface_id]
        if not isinstance(Surface, PlaneSurface):
            raise ValueError("chamfer requires planar stock carriers")
        Carriers[FaceValue.id] = Surface
        for UseId in Loops[LoopId]:
            if UseId in FinUses:
                raise ValueError("chamfer stock fin belongs to multiple face loops")
            FinUses[UseId] = FaceValue.id, Loops[LoopId]
    return FinUses, Carriers


# the selected incident face controls which signed traversal supplies both endpoint owners
def PickChmfRoles(StockValue: ChmfStockGeom, PickValue: ChmfEdgePlan) -> KChmfSupports:
    BodyValue = StockValue.SolidValue
    EdgeId = FindStockEdge(BodyValue, PickValue)
    EdgeUses, Opposite = ChmfFinLinks(BodyValue)
    Owners, Carriers = ChmfLoopOwners(BodyValue)
    if set(Owners) != set(Opposite):
        raise ValueError("chamfer fin is missing its actual stock loop")
    AxisName = "xyz"[PickValue.DistanceAxis]
    SideBit = PickValue.CornerBits[PickValue.DistanceAxis]
    CarrierStation = PickValue.BoundsValue[PickValue.DistanceAxis][SideBit]
    CarrierNormal = float(2 * SideBit - 1)
    HitUses = [
        FinValue.id
        for FinValue in EdgeUses[EdgeId]
        if IsClose(
            getattr(Carriers[Owners[FinValue.id][0]].normal, AxisName),
            CarrierNormal,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        and abs(
            getattr(Carriers[Owners[FinValue.id][0]].origin, AxisName) * 0.001
            - CarrierStation
        )
        <= 1e-12
    ]
    if len(HitUses) != 1:
        raise ValueError("chamfer distance face must match one actual incident carrier")
    (UseId,) = HitUses
    FaceId, LoopRing = Owners[UseId]
    Index = LoopRing.index(UseId)
    OtherId = Owners[Opposite[UseId]][0]
    StartId = Owners[Opposite[LoopRing[Index - 1]]][0]
    EndId = Owners[Opposite[LoopRing[(Index + 1) % len(LoopRing)]]][0]
    Roles = StockValue.FaceRoles
    if len({FaceId, OtherId, StartId, EndId}) != 4:
        raise ValueError("chamfer requires distinct incident and endpoint carriers")
    return Roles[FaceId], Roles[OtherId], Roles[StartId], Roles[EndId]
