from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarFace import (
    ReadPlanarFace,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


# tool caches contain separate solids and planar sheets whose owned loops must all resolve
def ReadCacheFaces(Table: LiveTable, BodyRef: int) -> tuple[FaceBoundary, ...]:
    BodyValue = RequireLive(Table, BodyRef, BodyNode)
    LumpValue = RequireLive(Table, BodyValue.FirstLump, LumpNode)
    ShellValue = RequireLive(Table, LumpValue.FirstShell, ShellNode)
    if (
        BodyValue.TransformRef != -1
        or LumpValue.NextLump != -1
        or ShellValue.NextShell != -1
        or StableRef(Table, LumpValue.OwnerBody) != BodyRef
        or StableRef(Table, ShellValue.OwnerLump)
        != StableRef(Table, BodyValue.FirstLump)
    ):
        raise ValueError("Native cut cache has unsupported body ownership")
    Current = ShellValue.FirstFace
    Results: list[FaceBoundary] = []
    SeenRefs: set[int] = set()
    while Current != -1:
        Current = StableRef(Table, Current)
        if Current in SeenRefs:
            raise ValueError("Native cut cache has cyclic face ownership")
        SeenRefs.add(Current)
        Results.append(
            ReadPlanarFace(
                Table, Current, StableRef(Table, LumpValue.FirstShell), AllowSheet=True
            )
        )
        Current = RequireLive(Table, Current, FaceNode).NextFace
    if not Results:
        raise ValueError("Native cut cache contains an empty body")
    return tuple(Results)
