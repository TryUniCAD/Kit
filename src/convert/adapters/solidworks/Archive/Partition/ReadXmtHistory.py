from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# legacy validation callers retain their original result after the shared mark checks
def ReadXmtHistory(DataValue: bytes, NodesValue: Mapping[int, XmtNode]) -> None:
    _ = ReadHistMarks(DataValue, NodesValue)
