from math import cos as Cosine, sin as SineValue, tau as FullTurn

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from interchange.geometry.Models.Transform import Transform


# framed periodic rims must retain the selected circle carrier and the original owned seam vertex
def CheckRimFrame(
    State: GeometryState, EdgeValue: EdgeNode, Frame: Transform, RadiusMm: float
) -> None:
    Curve = SnapEntity(State, EdgeValue.CurveRef, EllipseNode)
    Center = (Frame.origin.x / 10, Frame.origin.y / 10, Frame.origin.z / 10)
    AxisFirst = (Frame.x_axis.x, Frame.x_axis.y, Frame.x_axis.z)
    AxisSecond = (Frame.y_axis.x, Frame.y_axis.y, Frame.y_axis.z)
    RadiusCm = RadiusMm / 10
    SameNumbers(Curve.OriginCm, Center)
    SameNumbers(Curve.Normal, (Frame.z_axis.x, Frame.z_axis.y, Frame.z_axis.z))
    SameNumbers(Curve.MajorAxisCm, tuple(RadiusCm * Value for Value in AxisFirst))
    if (
        Curve.EllipseRatio != 1
        or Curve.LowerBound is not None
        or Curve.UpperBound is not None
    ):
        raise ValueError("Dual snapshot sheet requires an unbounded circular carrier")
    if (
        EdgeValue.StartVertex != EdgeValue.EndVertex
        or EdgeValue.Reversed
        or EdgeValue.Convexity != "unknown"
    ):
        raise ValueError(
            "Dual snapshot sheet has unsupported seam closure or orientation"
        )
    SameNumbers((EdgeValue.EndParam - EdgeValue.StartParam,), (FullTurn,))
    Vertex = SnapEntity(State, EdgeValue.StartVertex, VertexNode)
    Point = SnapEntity(State, Vertex.PointRef, PointNode)
    SameNumbers(
        Point.PositionCm,
        tuple(
            Origin
            + RadiusCm * Cosine(EdgeValue.StartParam) * First
            + RadiusCm * SineValue(EdgeValue.StartParam) * Second
            for Origin, First, Second in zip(Center, AxisFirst, AxisSecond, strict=True)
        ),
    )
