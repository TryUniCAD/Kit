from collections.abc import Mapping

from convert.Geometry.Parasolid import NativeId
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheShell import (
    ReadCacheShell,
)


# legacy face keys use encoded shorts while typed kernel references use decoded transmit indices
def ReadCacheFaces(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode
) -> dict[str, str]:
    Shell, Front = ReadCacheShell(NodesValue, BodyValue)
    Faces = WalkXmtChain(NodesValue, Shell.Integer("face"), 14)
    FrontIds = WalkXmtChain(
        NodesValue, Front.Integer("front_face"), 14, "next_front", "previous_front"
    )
    if not Faces or set(Faces) != set(FrontIds):
        raise ValueError("saved stock face sets differ across native shell sides")
    Result: dict[str, str] = {}
    for FaceIndex in Faces:
        FaceValue = NodesValue[FaceIndex]
        SurfaceIndex = FaceValue.Integer("surface")
        Surface = NodesValue.get(SurfaceIndex)
        if (
            FaceValue.Integer("shell") != Shell.IndexValue
            or FaceValue.Integer("front_shell") != Front.IndexValue
            or not 0 < FaceIndex < 32767
            or not 0 < SurfaceIndex < 32767
            or Surface is None
            or Surface.KindValue not in (50, 51)
        ):
            raise ValueError("saved stock face has alternate ownership or carrier")
        Result[NativeId("face", FaceIndex + 1)] = NativeId(
            "surface", SurfaceIndex + 1
        )
    return Result
