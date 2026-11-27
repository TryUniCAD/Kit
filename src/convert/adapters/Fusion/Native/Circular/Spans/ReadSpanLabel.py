from math import isclose as IsClose
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


# feature labels must identify physical cap stations and the selected side operation
def ReadSpanLabel(
    State: GeometryState,
    Entity: TagAttrib,
    Context: ExtrudeContext,
    Shape: CircleShape,
    Solid: FrustumBody,
    Operations: tuple[int, ...],
) -> tuple[str, float, str]:
    if not Operations or not Entity.Groups:
        raise ValueError("Native circular span labels require an owning operation")
    Lower = Solid.BasePoint[2] / 10
    Upper = Lower + Solid.Height / 10
    Primary = CurveTag(Shape.CurveNode)
    Owner = State.Entities[Entity.Links.OwnerRef]
    if isinstance(Owner, FaceNode):
        Surface = State.Entities[Owner.Surface]
        if isinstance(Surface, ConeNode):
            Label = Entity.Groups[0].PrimaryId
            if not Label.isdecimal() or Entity.Groups != tuple(
                FeatureTag(Label, (Value,)) for Value in Operations
            ):
                raise ValueError("Native circular span side label is malformed")
            return "side", 0.0, Label
        if not isinstance(Surface, PlaneNode):
            raise ValueError("Native circular span label owns an unsupported face")
        Level = Surface.OriginCm[2]
        RoleName = "cap"
    elif isinstance(Owner, EdgeNode):
        Level = SnapEntity(State, Owner.CurveRef, EllipseNode).OriginCm[2]
        RoleName = "edge"
    else:
        raise ValueError("Native circular span label has an unexpected owner")
    Station = Lower if IsClose(Level, Lower, rel_tol=0, abs_tol=1e-9) else Upper
    IsEnd = (Station == Lower) == (NumberValue(Context.Along.Fields["value"]) < 0)
    Expected = (
        ("2" if IsEnd else "1")
        if RoleName == "cap"
        else ("-1" if IsEnd or len(Operations) > 1 else "-" + str(Primary))
    )
    if not IsClose(Level, Station, rel_tol=0, abs_tol=1e-9) or Entity.Groups != (
        FeatureTag(Expected, Operations[:1]),
    ):
        raise ValueError(
            "Native circular span label identifies another physical station"
        )
    return RoleName, Station, ""
