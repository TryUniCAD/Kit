from dataclasses import replace as CopyData
from pathlib import Path as FilePath

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed


# a malformed archive must retain its container and geometry while changing only physical label ownership
def MakeBadLabel(Source: FilePath, Target: FilePath) -> None:
    Model = ReadDocument(Source.read_bytes())
    Snapshot = Model.Snapshots[0].Snapshot
    if not isinstance(Snapshot, GeometryState):
        raise ValueError("Label replay requires a typed geometry snapshot")
    CapRef, SheetRef, LabelRef = PickLabelSwap(Snapshot)
    Entities = list(Snapshot.Entities)
    CapFace, SheetFace, Label = Entities[CapRef], Entities[SheetRef], Entities[LabelRef]
    if (
        not isinstance(CapFace, FaceNode)
        or not isinstance(SheetFace, FaceNode)
        or not isinstance(Label, TagAttrib)
    ):
        raise ValueError("Label replay did not resolve face and attribute records")
    if (
        CapFace.Prefix.Attribute != LabelRef
        or SheetFace.Prefix.Attribute != -1
        or Label.Links.NextAttrib != -1
        or Label.Links.PriorAttrib != -1
    ):
        raise ValueError("Label replay requires independent attribute chains")
    Entities[CapRef] = CopyData(CapFace, Prefix=CopyData(CapFace.Prefix, Attribute=-1))
    Entities[SheetRef] = CopyData(
        SheetFace, Prefix=CopyData(SheetFace.Prefix, Attribute=LabelRef)
    )
    Entities[LabelRef] = CopyData(Label, Links=CopyData(Label.Links, OwnerRef=SheetRef))
    Snapshot = CopyData(Snapshot, Entities=tuple(Entities))
    _ = Target.write_bytes(
        EmitParsed(
            CopyData(
                Model, Snapshots=(CopyData(Model.Snapshots[0], Snapshot=Snapshot),)
            )
        )
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
