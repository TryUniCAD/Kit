from convert.Geometry.Parasolid import KLengthScale, TopologyRecord
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a replacement vertex must reach the same typed point that supplies its actual geometry
def CheckPointRow(
    OffsetValue: int, NodeValue: XmtNode, Record: TopologyRecord | None
) -> None:
    Expected = tuple(
        NodeValue.Integer(FieldName) + 1
        for FieldName in ("attributes_features", "owner", "next", "previous")
    )
    Position = tuple(
        CoordValue / KLengthScale for CoordValue in ReadXmtVector(NodeValue, "pvec")
    )
    if (
        Record is None
        or Record.point is None
        or Record.offset != OffsetValue
        or Record.attribute != NodeValue.IndexValue + 1
        or Record.references != Expected
        or (Record.point.x, Record.point.y, Record.point.z) != Position
    ):
        raise ValueError("current vertex point differs from its typed ownership")
