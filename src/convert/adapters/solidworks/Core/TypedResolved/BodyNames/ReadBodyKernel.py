from collections.abc import Mapping

from convert.Geometry.Parasolid import DecodePartData, ParaPayload
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the kernel body requires its actual versioned active and rollback graph before any public link
def ReadBodyKernel(
    StreamValue: bytes, StreamName: str
) -> tuple[tuple[ParaPayload, ...], Mapping[int, XmtNode], tuple[int, int]]:
    Payloads = DecodePartData(StreamValue, StreamName)
    if tuple(Payload.kind for Payload in Payloads) != ("partition", "deltas") or any(
        Payload.schema != "SCH_3701250_37102_13006" for Payload in Payloads
    ):
        raise ValueError(
            "selected body cache is not the witnessed active and rollback profile"
        )
    NodesValue = ReadActiveNodes(Payloads[0].data)
    CheckXmtGraph(NodesValue)
    MarksValue = ReadHistMarks(Payloads[1].data, NodesValue)
    return Payloads, NodesValue, MarksValue
