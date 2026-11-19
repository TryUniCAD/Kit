from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# both sides of the native boundary must belong to the same actual solid
def ReadBodyFaces(
    NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode, FaceCount: int = 6
) -> tuple[int, ...]:
    Regions = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("region"),
        19,
        OwnerField="body",
        OwnerValue=BodyValue.IndexValue,
    )
    if len(Regions) != 2 or set(Regions) != {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 19
    }:
        raise ValueError("named solid has an unqualified region inventory")
    VoidValue, SolidValue = (NodesValue[IndexValue] for IndexValue in Regions)
    if VoidValue.String("type") != "V" or SolidValue.String("type") != "S":
        raise ValueError("named solid has unqualified region roles")
    ShellValue = RequireXmt(NodesValue, SolidValue.Integer("shell"), 13)
    FrontValue = RequireXmt(NodesValue, VoidValue.Integer("shell"), 13)
    if (
        BodyValue.Integer("shell") != ShellValue.IndexValue
        or ShellValue.Integer("body") != BodyValue.IndexValue
        or FrontValue.Integer("body") != 0
        or ShellValue.Integer("region") != SolidValue.IndexValue
        or FrontValue.Integer("region") != VoidValue.IndexValue
        or {ShellValue.IndexValue, FrontValue.IndexValue}
        != {
            NodeValue.IndexValue
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue == 13
        }
    ):
        raise ValueError("named solid has foreign shell attachments")
    FaceIds = WalkXmtChain(NodesValue, ShellValue.Integer("face"), 14)
    FrontIds = WalkXmtChain(
        NodesValue,
        FrontValue.Integer("front_face"),
        14,
        "next_front",
        "previous_front",
    )
    if len(FaceIds) != FaceCount or set(FaceIds) != set(FrontIds):
        raise ValueError("named solid boundary is not the witnessed face profile")
    for IndexValue in FaceIds:
        FaceValue = NodesValue[IndexValue]
        if (
            FaceValue.Integer("shell") != ShellValue.IndexValue
            or FaceValue.Integer("front_shell") != FrontValue.IndexValue
        ):
            raise ValueError("named face has a foreign body side")
    return FaceIds
