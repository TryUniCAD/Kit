from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences


# complete active inventory prevents stray native records from being silently assigned to a named solid
def CheckXmtGraph(NodesValue: Mapping[int, XmtNode]) -> None:
    WorldValue = RequireXmt(NodesValue, 1, 101)
    if (
        WorldValue.Integer("alive") != 1
        or sum(NodeValue.KindValue == 101 for NodeValue in NodesValue.values()) != 1
        or any(
            IndexValue not in NodesValue
            for NodeValue in NodesValue.values()
            for IndexValue in XmtReferences(NodeValue)
        )
    ):
        raise ValueError("active native world has unresolved or ambiguous ownership")
