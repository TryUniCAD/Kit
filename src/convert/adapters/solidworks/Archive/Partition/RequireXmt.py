from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# every ownership edge must resolve to the required concrete kernel record class
def RequireXmt(
    NodesValue: Mapping[int, XmtNode], IndexValue: int, KindValue: int
) -> XmtNode:
    NodeValue = NodesValue.get(IndexValue)
    if NodeValue is None or NodeValue.KindValue != KindValue:
        raise ValueError("kernel reference has no matching typed owner")
    return NodeValue
