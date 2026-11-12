from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import (
    EdgeCurve,
    EdgeEnds,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.PlanBody import VertexKey


def DraftEdges(PlanValue: BodyPlan, FindIndex: DraftLookup) -> list[KDraftNode]:
    Ordinal = PlanValue.Ordinal
    Nodes: list[KDraftNode] = []
    for EdgeValue in PlanValue.Edges:
        Curve, Lower, Upper = EdgeCurve(EdgeValue)
        Start, Finish = (VertexKey(Point) for Point in EdgeEnds(EdgeValue))
        EdgeRef, CurveRef = ("edge", Ordinal, EdgeValue), ("curve", Ordinal, EdgeValue)
        NodeValue = EdgeNode(
            EntityPrefix(-1, -1),
            FindIndex(("vert", Ordinal, Start)),
            Lower,
            FindIndex(("vert", Ordinal, Finish)),
            Upper,
            FindIndex(PlanValue.EdgeOwners[EdgeValue]),
            FindIndex(CurveRef),
            False,
            "unknown",
        )
        Nodes.extend(((EdgeRef, NodeValue), (CurveRef, Curve)))
    for Point in PlanValue.Vertices:
        Owner, Index = PlanValue.VertexOwners[Point]
        Vertex = VertexNode(
            EntityPrefix(-1, -1),
            FindIndex(("edge", Ordinal, Owner)),
            Index,
            FindIndex(("point", Ordinal, Point)),
        )
        Nodes.append((("vert", Ordinal, Point), Vertex))
        Nodes.append(
            (("point", Ordinal, Point), PointNode(EntityPrefix(-1, -1), Point))
        )
    return Nodes
