from collections.abc import Mapping
from math import isfinite as IsFinite

from convert.Geometry.Parasolid import (
    KLengthScale,
    KMissingParam,
    ParseVertexUse,
    TopologyRecord,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a scanner vertex can represent a typed row only when both records agree on point ownership
def ReadVertexRow(
    BodyData: bytes, OffsetValue: int, NodeValue: XmtNode, Nodes: Mapping[int, XmtNode]
) -> TopologyRecord:
    PointValue = RequireXmt(Nodes, NodeValue.Integer("point"), 29)
    Tolerance = NodeValue.FieldsValue["tolerance"]
    if type(Tolerance) is not float or (
        Tolerance != KMissingParam and (not IsFinite(Tolerance) or Tolerance < 0.0)
    ):
        raise ValueError("current vertex tolerance is outside its typed domain")
    Expected = 0.0 if Tolerance == KMissingParam else Tolerance / KLengthScale
    Record = ParseVertexUse(BodyData, OffsetValue)
    if (
        PointValue.Integer("owner") != NodeValue.IndexValue
        or Record is None
        or Record.attribute != NodeValue.IndexValue + 1
        or Record.tolerance != Expected
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
