from math import cos as Cosine, sin as SineValue, hypot as Hypot, tau as FullTurn
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# complete circular rims preserve their seam positions and endpoint ownership
def CheckSpanRim(
    State: GeometryState,
    EdgeValue: EdgeNode,
    Center: tuple[float, float, float],
    Radius: float,
) -> None:
    Curve = SnapEntity(State, EdgeValue.CurveRef, EllipseNode)
    SameNumbers(Curve.OriginCm, Center)
    SameNumbers(Curve.Normal[:2], (0.0, 0.0))
    SameNumbers(
        (
            abs(Curve.Normal[2]),
            Curve.MajorAxisCm[2],
            Hypot(*Curve.MajorAxisCm[:2]),
            Curve.EllipseRatio,
        ),
        (1.0, 0.0, Radius, 1.0),
    )
    SameNumbers((EdgeValue.EndParam - EdgeValue.StartParam,), (FullTurn,))
    if (
        Curve.LowerBound is not None
        or Curve.UpperBound is not None
        or EdgeValue.StartVertex != EdgeValue.EndVertex
        or EdgeValue.Convexity != "unknown"
    ):
        raise ValueError("Native circular rim is trimmed or has inconsistent closure")
    Vertex = SnapEntity(State, EdgeValue.StartVertex, VertexNode)
    if Vertex.OwnerEdge != State.Entities.index(EdgeValue) or Vertex.EdgeIndex not in (
        0,
        2,
    ):
        raise ValueError("Native circular rim vertex belongs to another edge")
    Point = SnapEntity(State, Vertex.PointRef, PointNode)
    AxisX, AxisY = Curve.MajorAxisCm[:2]
    SameNumbers(
        Point.PositionCm,
        (
            Center[0]
            + AxisX * Cosine(EdgeValue.StartParam)
            - AxisY * Curve.Normal[2] * SineValue(EdgeValue.StartParam),
            Center[1]
            + AxisY * Cosine(EdgeValue.StartParam)
            + AxisX * Curve.Normal[2] * SineValue(EdgeValue.StartParam),
            Center[2],
        ),
    )
