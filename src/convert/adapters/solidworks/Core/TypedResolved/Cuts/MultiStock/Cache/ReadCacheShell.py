from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# each physical solid must keep both reciprocal sides of its own boundary
def ReadCacheShell(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode
) -> tuple[XmtNode, XmtNode]:
    Regions = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("region"),
        19,
        OwnerField="body",
        OwnerValue=BodyValue.IndexValue,
    )
    if len(Regions) != 2:
        raise ValueError("saved stock body has alternate native regions")
    VoidValue, SolidValue = (NodesValue[RegionId] for RegionId in Regions)
    Shell = RequireXmt(NodesValue, SolidValue.Integer("shell"), 13)
    Front = RequireXmt(NodesValue, VoidValue.Integer("shell"), 13)
    if (
        (VoidValue.String("type"), SolidValue.String("type")) != ("V", "S")
        or Shell.IndexValue != BodyValue.Integer("shell")
        or Shell.Integer("body") != BodyValue.IndexValue
        or Shell.Integer("region") != SolidValue.IndexValue
        or Front.Integer("body") != 0
        or Front.Integer("region") != VoidValue.IndexValue
        or Shell.Integer("next")
        or Front.Integer("next")
    ):
        raise ValueError("saved stock cache has alternate shell ownership")
    return Shell, Front
