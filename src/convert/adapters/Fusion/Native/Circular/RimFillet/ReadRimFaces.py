from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimUse import CheckRimUse
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapAccess import SnapEntity
from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import (
    BodyFaces,
    FaceCoedges,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# the complete shell traversal must account for every face loop and circular use exactly once
def ReadRimFaces(
    State: GeometryState,
    RootIndex: int,
    Surfaces: dict[int, str],
    Circles: dict[int, str],
    IsFinal: bool,
) -> dict[str, int]:
    BodyValue = SnapEntity(State, RootIndex, BodyNode)
    LumpValue = SnapEntity(State, BodyValue.FirstLump, LumpNode)
    ShellValue = SnapEntity(State, LumpValue.FirstShell, ShellNode)
    if (
        LumpValue.OwnerBody != RootIndex
        or ShellValue.OwnerLump != BodyValue.FirstLump
        or ShellValue.FirstWire != -1
    ):
        raise ValueError("Native rim shell has another body owner")
    Faces = BodyFaces(State, BodyValue)
    FaceRoles: dict[str, int] = {}
    SeenUses: set[int] = set()
    SeenLoops: set[int] = set()
    for FaceValue in Faces:
        Index = State.Entities.index(FaceValue)
        RoleName = Surfaces.get(FaceValue.Surface, "")
        if (
            not RoleName
            or RoleName in FaceRoles
            or FaceValue.DoubleSided
            or FaceValue.Contained is not None
            or FaceValue.Reversed != (RoleName == "bottom")
            or FaceValue.OwnerShell != LumpValue.FirstShell
        ):
            raise ValueError("Native rim face has an unsupported role or owner")
        FaceRoles[RoleName] = Index
        Coedges = FaceCoedges(State, FaceValue)
        if any(
            State.Entities.index(Coedge) in SeenUses or Coedge.OwnerLoop in SeenLoops
            for Coedge in Coedges
        ):
            raise ValueError("Native rim boundary use or loop has multiple owners")
        Roles = {
            CheckRimUse(State, Coedge, Index, RoleName, Circles, IsFinal)
            for Coedge in Coedges
        }
        Expected = (
            ({"bottom", "side"} if IsFinal else {"bottom", "top"})
            if RoleName == "side"
            else {"side", "top"} if RoleName == "blend" else {RoleName}
        )
        if Roles != Expected:
            raise ValueError("Native rim face joins another circular boundary")
        SeenUses.update(State.Entities.index(Coedge) for Coedge in Coedges)
        SeenLoops.update(Coedge.OwnerLoop for Coedge in Coedges)
    if set(FaceRoles) != (
        {"side", "blend", "top", "bottom"} if IsFinal else {"side", "top", "bottom"}
    ) or set(Faces) != {
        Entity for Entity in State.Entities if isinstance(Entity, FaceNode)
    }:
        raise ValueError("Native rim body omits physical faces")
    if SeenUses != {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, CoedgeNode)
    } or SeenLoops != {
        Index
        for Index, Entity in enumerate(State.Entities)
        if isinstance(Entity, LoopNode)
    }:
        raise ValueError("Native rim body omits boundary uses")
    return FaceRoles
