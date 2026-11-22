from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# the misplaced cap must coincide with an untagged sketch sheet so station coverage alone cannot detect it
def PickLabelSwap(State: GeometryState) -> tuple[int, int, int]:
    Sheets = tuple(
        Faces[0]
        for Entity in State.Entities
        if isinstance(Entity, BodyNode) and len(Faces := BodyFaces(State, Entity)) == 1
    )
    Matches: list[tuple[int, int, int]] = []
    for Index, Entity in enumerate(State.Entities):
        if (
            not isinstance(Entity, TagAttrib)
            or Entity.Links.NextAttrib != -1
            or Entity.Links.PriorAttrib != -1
        ):
            continue
        Owner = State.Entities[Entity.Links.OwnerRef]
        if (
            not isinstance(Owner, FaceNode)
            or Owner in Sheets
            or Owner.Prefix.Attribute != Index
        ):
            continue
        CapPlane = State.Entities[Owner.Surface]
        if not isinstance(CapPlane, PlaneNode):
            continue
        for Sheet in Sheets:
            Surface = State.Entities[Sheet.Surface]
            if (
                isinstance(Surface, PlaneNode)
                and Sheet.Prefix.Attribute == -1
                and Surface.Normal in ((0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
                and CapPlane.Normal in ((0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
                and CapPlane.OriginCm[2] == Surface.OriginCm[2]
            ):
                Matches.append(
                    (Entity.Links.OwnerRef, State.Entities.index(Sheet), Index)
                )
    if not Matches:
        raise ValueError(
            "Label replay requires an untagged sheet and independently labeled cap at the same station"
        )
    return min(Matches)
