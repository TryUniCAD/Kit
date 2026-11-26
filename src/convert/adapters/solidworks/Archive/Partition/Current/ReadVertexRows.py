from collections.abc import Mapping

from convert.Geometry.Parasolid import TopologyRecord
from convert.adapters.solidworks.Archive.Partition.Current.CheckPointRow import (
    CheckPointRow,
)
from convert.adapters.solidworks.Archive.Partition.Current.ReadVertexRow import (
    ReadVertexRow,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# full record extents distinguish a real vertex boundary from a fin payload coincidence
def ReadVertexRows(
    BodyData: bytes, Nodes: Mapping[int, XmtNode], Points: Mapping[int, TopologyRecord]
) -> tuple[dict[int, TopologyRecord], dict[int, list[tuple[int, int]]]]:
    Cursor = XmtCursor(BodyData)
    Vertices: dict[int, TopologyRecord] = {}
    FinSpans: dict[int, list[tuple[int, int]]] = {}
    while True:
        OffsetValue = Cursor.OffsetValue
        KindValue = Cursor.ReadKind()
        if KindValue == 1:
            break
        NodeValue = ReadXmtNodeMut(Cursor, KindValue)
        if KindValue == 17:
            FinSpans.setdefault(NodeValue.Integer("vertex") + 1, []).append(
                (OffsetValue, Cursor.OffsetValue)
            )
        elif KindValue == 18:
            Vertex = ReadVertexRow(BodyData, OffsetValue, NodeValue, Nodes)
            Vertices[Vertex.attribute] = Vertex
        elif KindValue == 29:
            CheckPointRow(OffsetValue, NodeValue, Points.get(NodeValue.IndexValue + 1))
    Cursor.FinishRead()
    return Vertices, FinSpans
