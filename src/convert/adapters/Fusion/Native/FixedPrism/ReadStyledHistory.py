from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import (
    CheckCuboid,
    CheckSignedMass,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.MaterialAttrib import (
    MaterialAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.States.LiveState import LiveState
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KFaceCorners


# styling must prove the same closed geometry and face identities in rollback and current states
def ReadStyleBody(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    MaterialTag: str,
    FaceRole: int,
) -> PlanarShell:
    History, Snapshot, (Active, Earlier, Unstyled), Height = ReadStyleInputs(
        Graph, Context, Model, Shape, MaterialTag, FaceRole
    )
    Lower, Upper = Snapshot.Frame.CornersCm[0], Snapshot.Frame.CornersCm[-1]
    SameNumbers(
        (*Lower, *Upper), (0.0, 0.0, 0.0, Shape.Width / 10, Shape.Depth / 10, Height)
    )
    OldTable = MakeLiveTable(History, Unstyled.StateId)
    OldShell = ReadStyledSolid(History, Snapshot, Unstyled.StateId)
    Owner = FaceAtRole(OldShell, Snapshot, FaceRole)
    OldFace = RequireLive(OldTable, Owner, FaceNode)
    OldTagSlot = OldFace.Prefix.Attribute
    OldTag = RequireLive(OldTable, OldTagSlot, TagAttrib)
    if OldTag.Links.OwnerRef != Owner or OldTag.Links.PriorAttrib != -1:
        raise ValueError("Native styled prism predecessor face tag disagrees")
    if any(
        isinstance(OldTable.Entities[SlotIndex], MaterialAttrib)
        for SlotIndex in OldTable.LiveSlots
    ):
        raise ValueError(
            "Native styled prism predecessor already contains a material attribute"
        )
    ActiveShell = ReadStyledSolid(History, Snapshot, Active.StateId)
    EarlierShell = ReadStyledSolid(History, Snapshot, Earlier.StateId)
    for StyledShell in (EarlierShell, ActiveShell):
        StyledTable = MakeLiveTable(History, StyledShell.StateId)
        if ReplaceData(StyledShell, StateId=Unstyled.StateId) != OldShell:
            raise ValueError("Native face styling changed the cuboid topology")
        CheckStyleDelta(OldTable, StyledTable, Owner, OldFace, OldTag, MaterialTag)
    CheckSignedMass(Context, Lower, Upper)
    return ActiveShell


# the source must bind a scoped appearance change to its original rollback states
def ReadStyleInputs(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    MaterialTag: str,
    FaceRole: int,
) -> tuple[JournalModel, PrismSnapshot, tuple[LiveState, LiveState, LiveState], float]:
    if len(Model.Bodies) != 1 or len(Model.Snapshots) != 1:
        raise ValueError("Native styled prism requires one history and one snapshot")
    History = Model.Bodies[0].History
    Snapshot = Model.Snapshots[0].Snapshot
    if not isinstance(History, JournalModel) or not isinstance(Snapshot, PrismSnapshot):
        raise ValueError(
            "Native styled prism requires its typed journal and prism snapshot"
        )
    if Graph.OneClass("Body") != Context.BodyNode or tuple(
        Entry.First
        for Entry in MappingItems(
            Context.BodyNode.Fields["faceVisualMaterialByAttrTagID"]
        )
    ) != (MaterialTag,):
        raise ValueError(
            "Native styled prism requires one owned design appearance mapping"
        )
    Height = NumberValue(Context.Along.Fields["value"])
    States = Materialize(History)
    if (
        len(States) != 4
        or type(FaceRole) is not int
        or not 0 <= FaceRole < len(KFaceCorners)
        or Height <= 0
        or Shape.BasePoint != (0.0, 0.0, 0.0)
    ):
        raise ValueError(
            "Native styled prism requires one positive origin-anchored cuboid"
        )
    Active, Earlier, Unstyled, Empty = States
    if (
        Active.StateId != History.Stream.CurrentStateId
        or Active.StateId != History.Stream.MaxStateId
        or Active.StateId != Context.Extrude.Fields["endModelHS"]
        or Empty.StateId != Context.Extrude.Fields["startModelHS"]
        or not Empty.StateId < Unstyled.StateId < Earlier.StateId < Active.StateId
        or Empty.Versions != ((0, 0),)
        or len(Active.Versions) != History.ActiveCount
    ):
        raise ValueError("Native styled prism rollback states disagree")
    return History, Snapshot, (Active, Earlier, Unstyled), Height


# the styled state may only add a face appearance and its reciprocal attribute links
def CheckStyleDelta(
    OldTable: LiveTable,
    StyledTable: LiveTable,
    Owner: int,
    OldFace: FaceNode,
    OldTag: TagAttrib,
    MaterialTag: str,
) -> None:
    OldTagSlot = OldFace.Prefix.Attribute
    StyledFace = RequireLive(StyledTable, Owner, FaceNode)
    NewSlot = StyledFace.Prefix.Attribute
    Attribute = RequireLive(StyledTable, NewSlot, MaterialAttrib)
    if (
        Attribute.Tag != MaterialTag
        or Attribute.Links.OwnerRef != Owner
        or Attribute.Links.PriorAttrib != -1
        or Attribute.Links.NextAttrib != OldTagSlot
        or set(StyledTable.LiveSlots) != {*OldTable.LiveSlots, NewSlot}
        or NewSlot in OldTable.LiveSlots
        or StyledFace
        != ReplaceData(OldFace, Prefix=ReplaceData(OldFace.Prefix, Attribute=NewSlot))
        or StyledTable.Entities[OldTagSlot]
        != ReplaceData(OldTag, Links=ReplaceData(OldTag.Links, PriorAttrib=NewSlot))
        or any(
            StyledTable.Entities[SlotIndex] != OldTable.Entities[SlotIndex]
            for SlotIndex in OldTable.LiveSlots
            if SlotIndex not in (Owner, OldTagSlot)
        )
    ):
        raise ValueError(
            "Native styled prism face appearance changed unrelated records"
        )


# independently traversed journal faces must match the saved snapshot roles and operation tags
def ReadStyledSolid(
    History: JournalModel, Snapshot: PrismSnapshot, StateId: int
) -> PlanarShell:
    Bodies = ReadPlanarState(History, StateId)
    if len(Bodies) != 1:
        raise ValueError("Native styled prism must own one live solid")
    (Shell,) = Bodies
    Table = MakeLiveTable(History, StateId)
    _ = CheckCuboid(
        Table, Shell, Snapshot.Frame.CornersCm[0], Snapshot.Frame.CornersCm[-1]
    )
    for FaceIndex, Expected in enumerate(Snapshot.TagSet.Faces):
        Owner = FaceAtRole(Shell, Snapshot, FaceIndex)
        FaceValue = RequireLive(Table, Owner, FaceNode)
        TagSlot = FaceValue.Prefix.Attribute
        Attribute = (
            Table.Entities[TagSlot] if 0 <= TagSlot < len(Table.Entities) else None
        )
        if isinstance(Attribute, MaterialAttrib):
            TagSlot = Attribute.Links.NextAttrib
        TagValue = RequireLive(Table, TagSlot, TagAttrib)
        if TagValue.Groups != (Expected,) or TagValue.Links.OwnerRef != Owner:
            raise ValueError(
                "Native styled prism journal and snapshot face tags disagree"
            )
    return Shell


# a face role comes from geometric incidence rather than vendor allocation order
def FaceAtRole(Shell: PlanarShell, Snapshot: PrismSnapshot, FaceRole: int) -> int:
    Corners = {Snapshot.Frame.CornersCm[Index] for Index in KFaceCorners[FaceRole]}
    Matches = tuple(
        FaceRef
        for FaceRef, RingValue in zip(Shell.FaceRefs, Shell.Rings, strict=True)
        if {Shell.PointsCm[Index] for Index in RingValue} == Corners
    )
    if len(Matches) != 1:
        raise ValueError(
            "Native styled prism face does not resolve to one snapshot role"
        )
    return Matches[0]
