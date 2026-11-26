from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# both endpoints of a line edge must be selected through the witnessed halfedges
def ReadEdgePoints(
    Nodes: Mapping[int, XmtNode], EdgeValue: XmtNode
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    FinValue = Nodes[EdgeValue.Integer("halfedge")]
    First = Nodes[FinValue.Integer("vertex")]
    Second = Nodes[Nodes[FinValue.Integer("other")].Integer("vertex")]
    return (
        ReadXmtVector(Nodes[First.Integer("point")], "pvec"),
        ReadXmtVector(Nodes[Second.Integer("point")], "pvec"),
    )
