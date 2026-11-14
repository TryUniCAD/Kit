from collections import Counter

from pytest import raises as Raises

from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.geometry.Parasolid import (
    DecodeBrepMut as DecodeBrepModel,
    EncodeBrepModel,
)
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepFace
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import KTransformIdentity, Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# reversed native segments still connect in profile membership order
def MakeRing(
    Corners: tuple[tuple[float, float], ...],
) -> tuple[LineGeometry, ...]:
    Points = tuple(PlaneVector(*Corner) for Corner in Corners)
    return tuple(
        LineGeometry(EndValue, Start) if Index % 2 else LineGeometry(Start, EndValue)
        for Index, (Start, EndValue) in enumerate(zip(Points, Points[1:] + Points[:1]))
    )


# a rectangular source establishes topology and opposite shared edge traversal
def CheckPrismBox() -> None:
    Profile = MakeRing(((0, 0), (0, 3), (4, 3), (4, 0)))
    Model, Volume, SurfaceArea, Bounds = BuildPrism(
        "box", KTransformIdentity, Profile, -1.0, 1.5
    )
    assert (Volume, SurfaceArea) == (30.0, 59.0)
    assert (Bounds.minimum, Bounds.maximum) == (
        SpaceVector(0.0, 0.0, -1.0),
        SpaceVector(4.0, 3.0, 1.5),
    )
    assert len(Model.bodies) == 1
    assert len(Model.vertices) == 8
    assert len(Model.edges) == len(Model.curves) == 12
    assert len(Model.faces) == len(Model.loops) == len(Model.surfaces) == 6
    assert len(Model.coedges) == 24
    assert Model.shells[0].closed
    assert Model.validate(frozenset(("box",))) == ()
    assert {(UseValue.edge_id, UseValue.reversed) for UseValue in Model.coedges} == {
        (EdgeValue.id, Reverse)
        for EdgeValue in Model.edges
        for Reverse in (False, True)
    }
    assert max(Counter(UseValue.edge_id for UseValue in Model.coedges).values()) == 2
    Normals: set[tuple[float, float, float]] = set()
    for Surface in Model.surfaces:
        assert isinstance(Surface, PlaneSurface)
        Normal = Surface.normal
        Origin = Surface.origin
        Normals.add((Normal.x, Normal.y, Normal.z))
        assert (
            (2.0 - Origin.x) * Normal.x
            + (1.5 - Origin.y) * Normal.y
            + (0.25 - Origin.z) * Normal.z
        ) < 0.0
    assert Normals == {
        (1.0, 0.0, 0.0),
        (-1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, -1.0),
    }


# concave cap area and translated component coordinates remain analytic
def CheckConcave() -> None:
    Profile = MakeRing(((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)))
    Frame = Transform(
        SpaceVector(4.0, 5.0, 6.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
    )
    Model, Volume, SurfaceArea, Bounds = BuildPrism("notch", Frame, Profile, -2.0, 0.0)
    assert (Volume, SurfaceArea) == (10.0, 34.0)
    assert (Bounds.minimum, Bounds.maximum) == (
        SpaceVector(2.0, 5.0, 6.0),
        SpaceVector(4.0, 8.0, 9.0),
    )
    assert len(Model.vertices) == 12
    assert len(Model.edges) == 18
    assert len(Model.faces) == 8
    assert len(Model.loops[0].coedge_ids) == 6
    assert len(Model.loops[1].coedge_ids) == 6
    assert Model.validate(frozenset(("notch",))) == ()


# malformed source loops and unsupported transforms fail before emitting any topology
def CheckPrismGuard() -> None:
    for Corners in (
        ((0, 0), (4, 4), (0, 4), (3, 0)),
        ((0, 0), (4, 0), (4, 4), (2, 0), (0, 4)),
    ):
        with Raises(ValueError, match="intersects itself"):
            _ = BuildPrism("cross", KTransformIdentity, MakeRing(Corners), 0.0, 1.0)
    with Raises(ValueError, match="collinear"):
        _ = BuildPrism(
            "flat",
            KTransformIdentity,
            MakeRing(((0, 0), (2, 0), (3, 0), (3, 4), (0, 4))),
            0.0,
            1.0,
        )
    Profile = MakeRing(((0, 0), (4, 0), (4, 3), (0, 3)))
    Broken = Profile[:-1] + (LineGeometry(PlaneVector(0, 3), PlaneVector(0, 1e-12)),)
    with Raises(ValueError, match="does not close"):
        _ = BuildPrism("open", KTransformIdentity, Broken, 0.0, 1.0)
    with Raises(ValueError, match="positive depth"):
        _ = BuildPrism("zero", KTransformIdentity, Profile, 1.0, 1.0)
    with Raises(ValueError, match="right handed"):
        _ = BuildPrism(
            "mirror", Transform(z_axis=SpaceVector(0.0, 0.0, -1.0)), Profile, 0.0, 1.0
        )
    with Raises(ValueError, match="loses precision"):
        _ = BuildPrism(
            "imprecise",
            Transform(origin=SpaceVector(0.0, 1e16, 0.0)),
            Profile,
            0.0,
            1.0,
        )


# loop winding against the face normal decides whether a kernel accepts a solid
def WindingDot(Model: BrepModel, FaceValue: BrepFace) -> float:
    Loops = {LoopValue.id: LoopValue for LoopValue in Model.loops}
    Coedges = {CoedgeValue.id: CoedgeValue for CoedgeValue in Model.coedges}
    Edges = {EdgeValue.id: EdgeValue for EdgeValue in Model.edges}
    Vertices = {VertexValue.id: VertexValue for VertexValue in Model.vertices}
    Surfaces = {SurfaceValue.id: SurfaceValue for SurfaceValue in Model.surfaces}
    Surface = Surfaces[FaceValue.surface_id]
    assert isinstance(Surface, PlaneSurface)
    Points: list[SpaceVector] = []
    for CoedgeId in Loops[FaceValue.loop_ids[0]].coedge_ids:
        CoedgeValue = Coedges[CoedgeId]
        EdgeValue = Edges[CoedgeValue.edge_id]
        VertexId = (
            EdgeValue.end_vertex_id
            if CoedgeValue.reversed
            else EdgeValue.start_vertex_id
        )
        Points.append(Vertices[VertexId].point)
    SumXValue = SumYValue = SumZValue = 0.0
    for Index, Start in enumerate(Points):
        NextPoint = Points[(Index + 1) % len(Points)]
        SumXValue += (Start.y - NextPoint.y) * (Start.z + NextPoint.z)
        SumYValue += (Start.z - NextPoint.z) * (Start.x + NextPoint.x)
        SumZValue += (Start.x - NextPoint.x) * (Start.y + NextPoint.y)
    Normal = Surface.normal
    return SumXValue * Normal.x + SumYValue * Normal.y + SumZValue * Normal.z


# encoding orients authored solids so every face winds against its surface normal
def TestBoxWinding() -> None:
    Profile = MakeRing(((0, 0), (0, 30), (40, 30), (40, 0)))
    Model, _, _, _ = BuildPrism("box", KTransformIdentity, Profile, 0.0, 20.0)
    Original = tuple(Model.loops[0].coedge_ids)
    PayloadData = EncodeBrepModel(Model, PartValue=False)
    assert tuple(Model.loops[0].coedge_ids) == Original
    Decoded = DecodeBrepModel(PayloadData)
    assert Decoded is not None
    assert (len(Decoded.faces), len(Decoded.loops)) == (6, 6)
    assert (len(Decoded.coedges), len(Decoded.edges), len(Decoded.vertices)) == (
        24,
        12,
        8,
    )
    assert all((WindingDot(Decoded, FaceValue) < 0.0) for FaceValue in Decoded.faces)
    assert EncodeBrepModel(Decoded, PartValue=False) == PayloadData
