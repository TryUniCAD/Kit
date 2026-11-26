from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Partition.XmtReferences import XmtReferences


# a local boundary requires one ordinary solid whose typed nodes are reachable
def ReadLocalRoot(
    NodesValue: Mapping[int, XmtNode],
) -> tuple[XmtNode, dict[int, set[int]]]:
    BodyValue = RequireXmt(NodesValue, 1, 12)
    KindsValue: dict[int, set[int]] = {}
    for NodeValue in NodesValue.values():
        KindsValue.setdefault(NodeValue.KindValue, set()).add(NodeValue.IndexValue)
    if (
        KindsValue[12] != {1}
        or BodyValue.Integer("body_type") != 1
        or any(
            BodyValue.Integer(NameValue)
            for NameValue in (
                "owner",
                "previous",
                "next",
                "child",
                "ref_instance",
                "lattice",
                "mesh",
                "polyline",
                "boundary_lattice",
                "boundary_mesh",
                "boundary_polyline",
            )
        )
    ):
        raise ValueError("local body is outside the ordinary solid representation")
    Pending = {BodyValue.IndexValue}
    Visited: set[int] = set()
    while Pending:
        IndexValue = Pending.pop()
        Visited.add(IndexValue)
        NodeValue = NodesValue[IndexValue]
        Pending.update(set(XmtReferences(NodeValue)) - Visited)
    if Visited != set(NodesValue):
        raise ValueError("local body has detached nodes")
    return BodyValue, KindsValue
