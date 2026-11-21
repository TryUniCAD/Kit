from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition


# saved cylinder identity cannot be inferred from a neutral face position or an incomplete kernel prefix
def ReadCylNodes(ArchiveValue: SldprtArchive) -> Mapping[int, XmtNode]:
    StreamName = "Contents/Config-0-Partition"
    PayloadsValue = DecodePartition(ArchiveValue.require(StreamName), StreamName)
    if tuple(Value.kind for Value in PayloadsValue) != ("partition", "deltas"):
        raise ValueError("concentric child requires the saved active and history pair")
    NodesValue = ReadActiveNodes(PayloadsValue[0].data)
    CheckXmtGraph(NodesValue)
    ReadXmtHistory(PayloadsValue[1].data, NodesValue)
    return NodesValue
