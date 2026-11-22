from typing import cast as CastValue

from dataclasses import dataclass as DataClass

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Extrude.Polygon.PrismRing import MeasureRing
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import (
    ChmfEdgePlan,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector


# the stock surface record distinguishes a cap ordinal from a sketch segment identity
@DataClass(frozen=True, slots=True)
class ChmfFaceRole:
    IsCap: bool
    NumberValue: int


# the physical stock geometry and its native lineage remain in the same ordered construction
@DataClass(frozen=True, slots=True)
class ChmfStockGeom:
    SolidValue: BrepModel
    FaceRoles: dict[str, ChmfFaceRole]


# the two faces at the actual finite edge come from the rectangle profile and cap extents
def ChmfEndpoints(EdgeValue: ChmfEdgePlan) -> tuple[KDatumVector, KDatumVector]:
    Values = list(EdgeValue.CornerBits)
    Result: list[KDatumVector] = []
    for Station in (0, 1):
        Values[EdgeValue.EdgeAxis] = Station
        XValue, YValue, ZValue = (
            Bounds[Index]
            for Bounds, Index in zip(EdgeValue.BoundsValue, Values, strict=True)
        )
        Result.append((XValue, YValue, ZValue))
    return Result[0], Result[1]


# surface lineage matches the actual source segment independently of ring reorientation
def ChmfSideKey(
    First: PlaneVector, Second: PlaneVector
) -> frozenset[tuple[float, float]]:
    return frozenset(((First.x, First.y), (Second.x, Second.y)))


# side carriers retain the segment identifiers that generated the physical stock
def ChmfFaceRoles(
    SolidValue: BrepModel,
    Points: tuple[PlaneVector, ...],
    PolyValue: PolygonGraph,
) -> dict[str, ChmfFaceRole]:
    Chords = zip(Points, Points[1:] + Points[:1], strict=True)
    SourceIds = {
        ChmfSideKey(First, Second): FieldInt(NodeValue.FieldsValue, "f08")
        for (First, Second), NodeValue in zip(Chords, PolyValue.LineValues, strict=True)
    }
    if len(SourceIds) != len(set(SourceIds.values())) or len(SourceIds) != 4:
        raise ValueError(
            "chamfer needs the four distinct actual stock sketch segment owners"
        )
    Ordered, _, _ = MeasureRing(Points)
    Sides = zip(Ordered, Ordered[1:] + Ordered[:1], strict=True)
    Start, EndFace, *Faces = SolidValue.faces
    Roles = {Start.id: ChmfFaceRole(True, 0), EndFace.id: ChmfFaceRole(True, 1)}
    for FaceValue, (First, Second) in zip(Faces, Sides, strict=True):
        Roles[FaceValue.id] = ChmfFaceRole(False, SourceIds[ChmfSideKey(First, Second)])
    return Roles


# the edge authority is rebuilt from the exact native rectangle producers own profile nodes
def MakeChmfStock(StockValue: PartCandidate) -> ChmfStockGeom:
    PlanValue, ProfileValue = StockValue.PlanValue, StockValue.ProfileValue
    PolyValue, FrameValue = ProfileValue.GeometryValue, ProfileValue.FrameValue
    if (
        not isinstance(CastValue(object, PlanValue), BlindPlan)
        or not isinstance(CastValue(object, PolyValue), PolygonGraph)
        or (
            FrameValue.OriginValue,
            FrameValue.AxisU,
            FrameValue.AxisV,
            FrameValue.NormalValue,
        )
        != ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    ):
        raise ValueError("chamfer stock must be its actual forward Front rectangle")
    Points = tuple(
        PlaneVector(XValue * 1000, YValue * 1000)
        for XValue, YValue in PlanValue.VerticesValue
    )
    Lines = tuple(
        LineGeometry(First, Second)
        for First, Second in zip(Points, Points[1:] + Points[:1], strict=True)
    )
    Solid, _, _, _ = BuildPrism(
        PlanValue.BodyId, Transform(), Lines, 0.0, PlanValue.DepthValue * 1000.0
    )
    return ChmfStockGeom(Solid, ChmfFaceRoles(Solid, Points, PolyValue))
