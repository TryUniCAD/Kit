from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# blind and through openings need the same perimeter cells with different cap ownership
def CheckRimSize(
    FaceCount: int, LoopCount: int, EdgeCount: int, VertexCount: int
) -> None:
    if FaceCount not in (10, 11) or (LoopCount, EdgeCount, VertexCount) != (12, 24, 16):
        raise ValueError("local pocket has an unsupported face or boundary inventory")


# each opening adds one terminated loop link inside its own cap face
def CheckPocketLoop(NodesValue: Mapping[int, XmtNode]) -> None:
    GroupsValue = tuple(
        WalkXmtChain(
            NodesValue,
            NodeValue.Integer("loop"),
            15,
            PreviousField=None,
            OwnerField="face",
            OwnerValue=NodeValue.IndexValue,
        )
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 14
    )
    Linked = tuple(
        IndexValue for GroupValue in GroupsValue for IndexValue in GroupValue
    )
    if (
        len(GroupsValue) not in (10, 11)
        or any(len(GroupValue) not in (1, 2) for GroupValue in GroupsValue)
        or len(Linked) != 12
        or set(Linked)
        != {Value.IndexValue for Value in NodesValue.values() if Value.KindValue == 15}
    ):
        raise ValueError("local pocket loop ownership differs from its rim")
