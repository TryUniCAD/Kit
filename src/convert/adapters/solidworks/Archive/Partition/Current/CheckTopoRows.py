from collections.abc import Iterable, Mapping

from convert.Geometry.Parasolid import TopologyRecord
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# a scanner row needs the actual boundary of the typed object it claims to represent
def CheckTopoRows(
    Selected: Iterable[int],
    Records: Mapping[int, TopologyRecord],
    KindValue: int,
    Nodes: Mapping[int, XmtNode],
    Spans: Mapping[int, tuple[int, int]],
) -> None:
    for IndexValue in Selected:
        Record = Records[IndexValue]
        NodeValue = RequireXmt(Nodes, IndexValue - 1, KindValue)
        if (
            Record.attribute != IndexValue
            or Record.offset != Spans[NodeValue.IndexValue][0]
        ):
            raise ValueError("used topology row differs from its typed record boundary")
