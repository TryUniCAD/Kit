from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# prior mark callers still rely on the original rollback selector contract
def ReadXmtHistory(DataValue: bytes, NodesValue: Mapping[int, XmtNode]) -> int:
    _, PriorMark = ReadHistMarks(DataValue, NodesValue)
    return PriorMark
