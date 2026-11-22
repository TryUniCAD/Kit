from typing import cast as CastValue

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Extrude.Polygon.PrismRing import MeasureRing, ReadPrismRing
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfEdgeRoles import (
    ChmfFinLinks,
    ChmfLoopOwners,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import (
    ChmfSideKey,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfPartRead import (
    ChmfEdgeRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import BrepCoedge
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

# finite stock point coordinates retain their model space axis order
KChmfCoords = tuple[float, float, float]


# physical faces inherit the actual permanent line or signed cap independently of array order
def ReadChmfRoleMap(
    BodyValue: BrepModel,
    PrismValue: PrismPlan,
    LoopValue: LineLoop,
) -> dict[str, KChmfRoleKey]:
    Ordered, _, _ = MeasureRing(ReadPrismRing(PrismValue.LinesValue))
    Lines = {
        ChmfSideKey(
            PlaneVector(*LoopValue.PointsValue[LineValue.StartValue].PositionValue),
            PlaneVector(*LoopValue.PointsValue[LineValue.EndValue].PositionValue),
        ): LineValue.PermanentId
        for LineValue in LoopValue.LinesValue
    }
    LowFace, HighFace, *Sides = BodyValue.faces
    Result: dict[str, KChmfRoleKey] = {
        LowFace.id: ("moEndFaceSurfIdRep_c", 0, 0),
        HighFace.id: ("moEndFaceSurfIdRep_c", 1, 0),
    }
    for FaceValue, First, Second in zip(
        Sides, Ordered, Ordered[1:] + Ordered[:1], strict=True
    ):
        Result[FaceValue.id] = (
            "moFromSktEntSurfIdRep_c",
            Lines[ChmfSideKey(First, Second)],
            None,
        )
    if len(set(Result.values())) != 6:
        raise ValueError("chamfer stock geometry has ambiguous permanent face roles")
    return Result


# each candidate fin must supply the same two incident and two endpoint roles in archive order
def PickChmfFin(
    BodyValue: BrepModel,
    FaceRoles: dict[str, KChmfRoleKey],
    KeysValue: tuple[KChmfRoleKey, ...],
) -> tuple[BrepCoedge, str]:
    _, Opposites = ChmfFinLinks(BodyValue)
    Owners, _ = ChmfLoopOwners(BodyValue)
    Matches: list[tuple[BrepCoedge, str]] = []
    for FinValue in BodyValue.coedges:
        FaceId, LoopRing = Owners[FinValue.id]
        if FaceRoles[FaceId] != KeysValue[0]:
            continue
        IndexValue = LoopRing.index(FinValue.id)
        Roles = (
            FaceRoles[FaceId],
            FaceRoles[Owners[Opposites[FinValue.id]][0]],
            FaceRoles[Owners[Opposites[LoopRing[IndexValue - 1]]][0]],
            FaceRoles[Owners[Opposites[LoopRing[(IndexValue + 1) % len(LoopRing)]]][0]],
        )
        if Roles == KeysValue:
            Matches.append((FinValue, FaceId))
    if len(Matches) != 1:
        raise ValueError(
            "chamfer roles do not select one actual signed finite stock edge"
        )
    return Matches[0]


# neutral witnesses use actual physical coordinates only after signed surface correspondence
def ProjectChmfEdge(
    BodyValue: BrepModel,
    Bounds: BoundingBox,
    FinValue: BrepCoedge,
    FaceId: str,
) -> ChmfEdgeRead:
    _, Planes = ChmfLoopOwners(BodyValue)
    (EdgeNode,) = (Value for Value in BodyValue.edges if Value.id == FinValue.edge_id)
    Vertices = {Value.id: Value.point for Value in BodyValue.vertices}
    First = CoordsChmf(Vertices[EdgeNode.start_vertex_id])
    Second = CoordsChmf(Vertices[EdgeNode.end_vertex_id])
    Normal = CoordsChmf(Planes[FaceId].normal)
    (EdgeAxis,) = (
        Index
        for Index, (Front, Second) in enumerate(zip(First, Second, strict=True))
        if Front != Second
    )
    (SideAxis,) = (Index for Index, Value in enumerate(Normal) if abs(Value) == 1.0)
    Lower, Upper = CoordsChmf(Bounds.minimum), CoordsChmf(Bounds.maximum)
    CornerBits = tuple(
        (
            -1
            if Index == EdgeAxis
            else 0 if Value == Lower[Index] else 1 if Value == Upper[Index] else -2
        )
        for Index, Value in enumerate(First)
    )
    if (
        -2 in CornerBits
        or SideAxis == EdgeAxis
        or Normal[SideAxis] != float(2 * CornerBits[SideAxis] - 1)
    ):
        raise ValueError(
            "chamfer selected carrier disagrees with the signed stock extremes"
        )
    EdgePoint = SpaceVector(
        *(Front / 2 + Second / 2 for Front, Second in zip(First, Second, strict=True))
    )
    FacePoint = SpaceVector(
        *(
            First[Index] if Index == SideAxis else Lower[Index] / 2 + Upper[Index] / 2
            for Index in range(3)
        )
    )
    return ChmfEdgeRead(
        EdgePoint,
        FacePoint,
        EdgeAxis,
        SideAxis,
        CastValue(tuple[int, int, int], CornerBits),
        Bounds,
    )


# typed three space points need no inferred native coordinate system
def CoordsChmf(PointValue: SpaceVector) -> KChmfCoords:
    return PointValue.x, PointValue.y, PointValue.z


# recovering a selected edge starts from the same analytic prism as the measured constructor
def JoinChmfEdge(
    PrismValue: PrismPlan,
    LoopValue: LineLoop,
    KeysValue: tuple[KChmfRoleKey, ...],
) -> ChmfEdgeRead:
    BodyValue, _, _, Bounds = BuildPrism(
        "stock",
        PrismValue.FrameValue,
        PrismValue.LinesValue,
        0.0,
        PrismValue.DepthValue,
    )
    FaceRoles = ReadChmfRoleMap(BodyValue, PrismValue, LoopValue)
    FinValue, FaceId = PickChmfFin(BodyValue, FaceRoles, KeysValue)
    return ProjectChmfEdge(BodyValue, Bounds, FinValue, FaceId)
