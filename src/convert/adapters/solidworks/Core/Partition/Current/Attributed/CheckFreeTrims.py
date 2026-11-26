from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckOwnedTrim import (
    CheckOwnedTrim,
)


# all nonboundary trim carriers and their reverse links need explicit owners
def CheckFreeTrims(
    Nodes: Mapping[int, XmtNode], BodyValue: XmtNode, Kinds: Mapping[int, set[int]]
) -> None:
    Trims = WalkXmtChain(
        Nodes,
        BodyValue.Integer("curve"),
        133,
        OwnerField="owner",
        OwnerValue=BodyValue.IndexValue,
    )
    if not Trims or set(Trims) != Kinds.get(133):
        raise ValueError("attributed active trim roster is incomplete")
    Owners = {CheckOwnedTrim(Nodes, Nodes[IndexValue]) for IndexValue in Trims}
    if Owners != Kinds.get(141) or len(Owners) != len(Trims):
        raise ValueError("attributed active geometric ownership is ambiguous")
    if {
        NodeValue.Integer("geometric_owner")
        for NodeValue in Nodes.values()
        if NodeValue.KindValue == 30 and NodeValue.Integer("geometric_owner")
    } != Owners or sum(
        bool(NodeValue.Integer("geometric_owner"))
        for NodeValue in Nodes.values()
        if NodeValue.KindValue == 30
    ) != len(
        Owners
    ):
        raise ValueError("attributed active line roster has foreign geometric owners")
