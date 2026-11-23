from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the rim adds one terminated loop link inside the same face owner
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
        sorted(map(len, GroupsValue)) != [1] * 10 + [2]
        or len(Linked) != 12
        or set(Linked)
        != {Value.IndexValue for Value in NodesValue.values() if Value.KindValue == 15}
    ):
        raise ValueError("local pocket loop ownership differs from its rim")
