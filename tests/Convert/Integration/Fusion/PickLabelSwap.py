from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# the misplaced cap must coincide with the sketch sheet so station coverage alone cannot detect it
def PickLabelSwap(State: GeometryState) -> tuple[int, int, int]:
    Sheets = tuple(
        Faces[0]
        for Entity in State.Entities
        if isinstance(Entity, BodyNode) and len(Faces := BodyFaces(State, Entity)) == 1
    )
    if len(Sheets) != 1:
        raise ValueError("Label replay requires one sketch sheet")
    Surface = State.Entities[Sheets[0].Surface]
    if not isinstance(Surface, PlaneNode):
        raise ValueError("Label replay requires a planar sketch sheet")
    for Index, Entity in enumerate(State.Entities):
        if not isinstance(Entity, TagAttrib):
            continue
        Owner = State.Entities[Entity.Links.OwnerRef]
        if not isinstance(Owner, FaceNode) or Owner in Sheets:
            continue
        CapPlane = State.Entities[Owner.Surface]
        if (
            isinstance(CapPlane, PlaneNode)
            and CapPlane.OriginCm[2] == Surface.OriginCm[2]
        ):
            return Entity.Links.OwnerRef, State.Entities.index(Sheets[0]), Index
    raise ValueError("Label replay has no cap at the sketch station")
