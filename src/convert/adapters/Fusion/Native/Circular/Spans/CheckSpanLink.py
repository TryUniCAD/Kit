from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanRim import CheckSpanRim
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# sketch source links must retain the selected circle and physical reference plane
def CheckSpanLink(
    State: GeometryState, Entity: SketchAttrib, Shape: CircleShape
) -> None:
    Owner = State.Entities[Entity.Links.OwnerRef]
    if isinstance(Owner, EdgeNode):
        EdgeValue = Owner
        Direction = 1
    elif isinstance(Owner, CoedgeNode):
        EdgeValue = SnapEntity(State, Owner.EdgeRef, EdgeNode)
        Direction = 0
    else:
        raise ValueError("Native circular source link has an unexpected owner")
    if Entity.SourceLink != SketchLink(CurveTag(Shape.CurveNode), 0, Direction, 1, 1):
        raise ValueError("Native circular source link belongs to another curve")
    CheckSpanRim(
        State,
        EdgeValue,
        (Shape.Geometry.center.x / 10, Shape.Geometry.center.y / 10, 0.0),
        Shape.Geometry.radius / 10,
    )
