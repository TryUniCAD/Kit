from convert.adapters.Fusion.Native.Circular.Spans.CheckTagOwners import CheckTagOwners
from convert.adapters.Fusion.Native.Circular.Spans.CheckBodyTag import CheckBodyTag
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanLabel import ReadSpanLabel
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanLink import CheckSpanLink


# complete topology and sketch ownership must be present without duplicated physical labels
def CheckSpanTags(
    State: GeometryState,
    Context: ExtrudeContext,
    Shape: CircleShape,
    Solid: FrustumBody,
    Operations: tuple[int, ...],
    HasBodyTag: bool,
) -> str:
    CheckTagOwners(State)
    Labels: dict[tuple[str, float], str] = {}
    SeenOwners: set[int] = set()
    SketchOwners: set[int] = set()
    BodyTags = 0
    for Entity in State.Entities:
        if isinstance(Entity, TagAttrib):
            if not Entity.Groups or Entity.Links.OwnerRef in SeenOwners:
                raise ValueError("Native circular span has duplicated feature labels")
            SeenOwners.add(Entity.Links.OwnerRef)
            if isinstance(State.Entities[Entity.Links.OwnerRef], BodyNode):
                BodyTags += 1
                CheckBodyTag(Entity, Operations)
                continue
            RoleName, Station, Primary = ReadSpanLabel(
                State, Entity, Context, Shape, Solid, Operations
            )
            if (RoleName, Station) in Labels:
                raise ValueError(
                    "Native circular span repeats a physical topology label"
                )
            Labels[(RoleName, Station)] = Primary
        elif isinstance(Entity, SketchAttrib):
            if Entity.Links.OwnerRef in SketchOwners:
                raise ValueError("Native circular span repeats a sketch source link")
            SketchOwners.add(Entity.Links.OwnerRef)
            CheckSpanLink(State, Entity, Shape)
    Lower, Upper = Solid.BasePoint[2] / 10, Solid.BasePoint[2] / 10 + Solid.Height / 10
    if set(Labels) != {
        ("side", 0.0),
        ("cap", Lower),
        ("cap", Upper),
        ("edge", Lower),
        ("edge", Upper),
    } or BodyTags != int(HasBodyTag):
        raise ValueError("Native circular span topology label coverage is incomplete")
    return Labels[("side", 0.0)]
