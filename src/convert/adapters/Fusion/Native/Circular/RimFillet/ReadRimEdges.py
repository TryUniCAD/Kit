from math import pi as CirclePi

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# every orbit retains its exact seam vertex parameter interval and physical tangency
def ReadRimEdges(
    State: GeometryState, Circles: dict[int, str], IsFinal: bool
) -> dict[str, int]:
    Roles: dict[str, int] = {}
    for Index, Entity in enumerate(State.Entities):
        if not isinstance(Entity, EdgeNode):
            continue
        RoleName = Circles.get(Entity.CurveRef, "")
        if (
            not RoleName
            or RoleName in Roles
            or Entity.StartVertex != Entity.EndVertex
            or Entity.Reversed
            or Entity.Convexity
            != ("unknown" if RoleName == "bottom" or not IsFinal else "tangent")
        ):
            raise ValueError("Native rim edge has another role or parameter direction")
        SameNumbers((Entity.StartParam, Entity.EndParam), (-CirclePi, CirclePi))
        if SnapEntity(State, Entity.OwnerCoedge, CoedgeNode).EdgeRef != Index:
            raise ValueError("Native rim edge has another owner")
        Vertex = SnapEntity(State, Entity.StartVertex, VertexNode)
        CurveValue = SnapEntity(State, Entity.CurveRef, EllipseNode)
        if Vertex.OwnerEdge != Index or Vertex.EdgeIndex not in (0, 2):
            raise ValueError("Native rim seam vertex has another owner")
        PointValue = SnapEntity(State, Vertex.PointRef, PointNode)
        SameNumbers(
            PointValue.PositionCm,
            (-CurveValue.MajorAxisCm[0], 0.0, CurveValue.OriginCm[2]),
        )
        Roles[RoleName] = Index
    if {
        Entity.CurveRef for Entity in State.Entities if isinstance(Entity, EdgeNode)
    } != set(Circles) or {
        Entity.StartVertex for Entity in State.Entities if isinstance(Entity, EdgeNode)
    } != {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, VertexNode)
    }:
        raise ValueError("Native rim orbits omit carriers or vertices")
    if {
        Entity.PointRef for Entity in State.Entities if isinstance(Entity, VertexNode)
    } != {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, PointNode)
    }:
        raise ValueError("Native rim vertices omit saved points")
    return Roles
