from dataclasses import replace as CopyData
from pathlib import Path as FilePath

from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

# offset caps need a separate misplaced label witness because neither cap coincides with the sketch
def MakeOffsetLabel(Source: FilePath, Target: FilePath) -> None:
    Model = ReadDocument(Source.read_bytes())
    State = Model.Snapshots[0].Snapshot
    assert isinstance(State, GeometryState)
    Sheet = next(
        Faces[0]
        for Entity in State.Entities
        if isinstance(Entity, BodyNode)
        and len(Faces := BodyFaces(State, Entity)) == 1
        and Faces[0].Prefix.Attribute == -1
    )
    LabelIndex, Label = next(
        (Index, Entity)
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, TagAttrib)
        and isinstance(State.Entities[Entity.Links.OwnerRef], FaceNode)
        and Entity.Links.NextAttrib == Entity.Links.PriorAttrib == -1
    )
    Owner = State.Entities[Label.Links.OwnerRef]
    assert isinstance(Owner, FaceNode) and Owner.Prefix.Attribute == LabelIndex
    Entities = list(State.Entities)
    SheetIndex = State.Entities.index(Sheet)
    Entities[Label.Links.OwnerRef] = CopyData(
        Owner, Prefix=CopyData(Owner.Prefix, Attribute=-1)
    )
    Entities[SheetIndex] = CopyData(
        Sheet, Prefix=CopyData(Sheet.Prefix, Attribute=LabelIndex)
    )
    Entities[LabelIndex] = CopyData(
        Label, Links=CopyData(Label.Links, OwnerRef=SheetIndex)
    )
    Snapshot = CopyData(
        Model.Snapshots[0], Snapshot=CopyData(State, Entities=tuple(Entities))
    )
    _ = Target.write_bytes(EmitParsed(CopyData(Model, Snapshots=(Snapshot,))))
