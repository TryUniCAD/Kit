from math import cos as Cosine, sin as SineValue, tau as FullTurn

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# shared closed rims require reciprocal uses and the actual saved circle seam
def CheckDualRims(State: GeometryState) -> None:
    for Index, Entity in enumerate(State.Entities):
        if isinstance(Entity, CoedgeNode):
            Partner = State.Entities[Entity.Partner]
            assert isinstance(Partner, CoedgeNode)
            assert Partner.Partner == Index and Partner.EdgeRef == Entity.EdgeRef
            assert Partner.Reversed != Entity.Reversed
        if not isinstance(Entity, EdgeNode):
            continue
        Curve = State.Entities[Entity.CurveRef]
        assert isinstance(Curve, EllipseNode)
        SameNumbers((Entity.EndParam - Entity.StartParam,), (FullTurn,))
        assert Curve.LowerBound is Curve.UpperBound is None
        assert Entity.StartVertex == Entity.EndVertex
        Vertex = State.Entities[Entity.StartVertex]
        assert isinstance(Vertex, VertexNode)
        assert Vertex.OwnerEdge == Index and Vertex.EdgeIndex in (0, 2)
        Point = State.Entities[Vertex.PointRef]
        assert isinstance(Point, PointNode)
        Normal, Major = Curve.Normal, Curve.MajorAxisCm
        Minor = (
            Normal[1] * Major[2] - Normal[2] * Major[1],
            Normal[2] * Major[0] - Normal[0] * Major[2],
            Normal[0] * Major[1] - Normal[1] * Major[0],
        )
        SameNumbers(
            Point.PositionCm,
            tuple(
                Origin
                + Along * Cosine(Entity.StartParam)
                + Across * SineValue(Entity.StartParam)
                for Origin, Along, Across in zip(
                    Curve.OriginCm, Major, Minor, strict=True
                )
            ),
        )
