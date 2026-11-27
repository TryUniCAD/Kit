from collections import Counter

from convert.adapters.Fusion.Native.Circular.DualSnapshots.SnapBodyFaces import (
    SnapBodyFaces,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import (
    BodyClosure,
)
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# complete sheet correspondence must retain source attribution without accepting unused or unexpected records
def CheckSheetBody(State: GeometryState, RootId: int, CircleId: int) -> tuple[int, ...]:
    BodyValue = SnapEntity(State, RootId, BodyNode)
    _ = SnapBodyFaces(State, BodyValue)
    Closure = BodyClosure(State, RootId)
    Expected: dict[type[object], int] = {
        ClassType: 1
        for ClassType in (
            BodyNode,
            LumpNode,
            ShellNode,
            FaceNode,
            LoopNode,
            CoedgeNode,
            EdgeNode,
            VertexNode,
            PointNode,
            PlaneNode,
            EllipseNode,
        )
    }
    Expected[SketchAttrib] = 2
    if BodyValue.TransformRef != -1:
        Expected[TransformNode] = 1
    if Counter(type(State.Entities[Identity]) for Identity in Closure) != Expected:
        raise ValueError("Dual snapshot sheet has unexpected topology or attributes")
    for Identity in Closure:
        Entity = State.Entities[Identity]
        if isinstance(Entity, (EdgeNode, CoedgeNode)):
            Attribute = SnapEntity(State, Entity.Prefix.Attribute, SketchAttrib)
            if Attribute.SourceLink != SketchLink(
                CircleId, 0, int(isinstance(Entity, EdgeNode)), 1, 1
            ) or (
                Attribute.Links.OwnerRef,
                Attribute.Links.NextAttrib,
                Attribute.Links.PriorAttrib,
            ) != (
                Identity,
                -1,
                -1,
            ):
                raise ValueError(
                    "Dual snapshot sheet source does not identify its selected circle"
                )
        elif not isinstance(Entity, SketchAttrib) and MakeEntityNode(Entity).Tokens[
            0
        ] != (12, -1):
            raise ValueError("Dual snapshot sheet has an unexpected attribute owner")
        if isinstance(Entity, VertexNode) and Entity.EdgeIndex != 0:
            raise ValueError(
                "Dual snapshot sheet seam has an unsupported endpoint role"
            )
        if isinstance(Entity, CoedgeNode) and Entity.Pcurve != -1:
            raise ValueError("Dual snapshot sheet has an unsupported parameter curve")
    return Closure
