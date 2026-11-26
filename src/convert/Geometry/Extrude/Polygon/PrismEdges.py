from math import hypot as Hypot, isclose as IsClose

from convert.Geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


# rim and rail edges retain shared endpoints for exact cap and wall connectivity
def BuildPrismEdges(
    Prefix: str,
    FrameValue: Transform,
    Points: tuple[PlaneVector, ...],
    LowerMm: float,
    UpperMm: float,
    UpperPoints: tuple[PlaneVector, ...] | None = None,
) -> tuple[tuple[BrepVertex, ...], tuple[LineCurve, ...], tuple[BrepEdge, ...]]:
    Count = len(Points)
    Outlines = (Points, Points if UpperPoints is None else UpperPoints)
    if len(Outlines[1]) != Count:
        raise ValueError("Extrude prism cap vertex counts disagree")
    Vertices = tuple(
        BrepVertex(
            f"{Prefix}-vertex-{Station * Count + Index}",
            PlacePrismPoint(FrameValue, PointValue, Height),
        )
        for Station, (Height, Outline) in enumerate(
            zip((LowerMm, UpperMm), Outlines, strict=True)
        )
        for Index, PointValue in enumerate(Outline)
    )
    Segments = (
        tuple((Index, (Index + 1) % Count) for Index in range(Count))
        + tuple((Count + Index, Count + (Index + 1) % Count) for Index in range(Count))
        + tuple((Index, Count + Index) for Index in range(Count))
    )
    RimLengths = tuple(
        Hypot(Second.x - First.x, Second.y - First.y)
        for Outline in Outlines
        for First, Second in zip(Outline, Outline[1:] + Outline[:1], strict=True)
    )
    Lengths = RimLengths + tuple(
        Hypot(Second.x - First.x, Second.y - First.y, UpperMm - LowerMm)
        for First, Second in zip(*Outlines, strict=True)
    )
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    for Index, (Start, Finish) in enumerate(Segments):
        First, Second = Vertices[Start], Vertices[Finish]
        DeltaX = Second.point.x - First.point.x
        DeltaY = Second.point.y - First.point.y
        DeltaZ = Second.point.z - First.point.z
        Length = Hypot(DeltaX, DeltaY, DeltaZ)
        if not IsClose(Length, Lengths[Index], rel_tol=1e-8, abs_tol=0.0):
            raise ValueError("Extrude prism edge loses precision in the spatial frame")
        CurveId = f"{Prefix}-curve-{Index}"
        Curves.append(
            LineCurve(
                CurveId,
                First.point,
                SpaceVector(DeltaX / Length, DeltaY / Length, DeltaZ / Length),
            )
        )
        Edges.append(
            BrepEdge(
                f"{Prefix}-edge-{Index}", First.id, Second.id, CurveId, 0.0, Length
            )
        )
    return Vertices, tuple(Curves), tuple(Edges)
