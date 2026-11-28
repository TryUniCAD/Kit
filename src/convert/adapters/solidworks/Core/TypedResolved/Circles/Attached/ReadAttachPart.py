from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import DecodePartition


# an attached physical body needs the active frame and its rollback companion
def ReadAttachPart(Partition: bytes) -> tuple[bytes, bytes, Mapping[int, XmtNode]]:
    Active, History = DecodePartition(Partition, KPartitionStream)
    if (Active.kind, History.kind) != ("partition", "deltas"):
        raise ValueError(
            "SOLIDWORKS attached circle lacks its unique active and rollback states"
        )
    Nodes = ReadActiveNodes(Active.data)
    CheckXmtGraph(Nodes)
    return Active.data, History.data, Nodes
