from collections.abc import Mapping

from convert.Geometry.Parasolid import ParseVertexUse, TopologyRecord
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a scanner vertex can represent a typed row only when both records agree on point ownership
def ReadVertexRow(
    BodyData: bytes, OffsetValue: int, NodeValue: XmtNode, Nodes: Mapping[int, XmtNode]
) -> TopologyRecord:
    PointValue = RequireXmt(Nodes, NodeValue.Integer("point"), 29)
    Record = ParseVertexUse(BodyData, OffsetValue)
    if (
        PointValue.Integer("owner") != NodeValue.IndexValue
        or Record is None
        or Record.attribute != NodeValue.IndexValue + 1
        or Record.references[:5]
        != tuple(
            NodeValue.Integer(FieldName) + 1
            for FieldName in (
                "attributes_features",
                "halfedge",
                "previous",
                "next",
                "point",
            )
        )
    ):
        raise ValueError("current vertex row differs from its typed ownership")
    return Record
