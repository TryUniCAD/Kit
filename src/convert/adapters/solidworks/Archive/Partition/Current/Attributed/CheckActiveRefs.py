from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.Current.Attributed.AttributedRefs import (
    AttributedRefs,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a matching typed record cannot provide geometry unless the selected world owns it
def CheckActiveRefs(Nodes: Mapping[int, XmtNode]) -> None:
    World = RequireXmt(Nodes, 1, 101)
    if (
        World.Integer("alive") != 1
        or sum(NodeValue.KindValue == 101 for NodeValue in Nodes.values()) != 1
    ):
        raise ValueError("attributed active world ownership is ambiguous")
    Pending = {World.IndexValue}
    SeenIndices: set[int] = set()
    while Pending:
        IndexValue = Pending.pop()
        SeenIndices.add(IndexValue)
        Pending.update(set(AttributedRefs(Nodes, Nodes[IndexValue])) - SeenIndices)
    if SeenIndices != set(Nodes):
        raise ValueError("attributed active graph has detached records")
