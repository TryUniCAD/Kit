from collections.abc import Sequence

from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from interchange.Payloads.PayloadRecord import BrepPayload


# an exact payload group prevents the local solid from replacing active geometry
def ReadLocalPay(Payloads: Sequence[BrepPayload]) -> bytes:
    StreamsValue = {
        (Payload.source_stream, Payload.kind): Payload.data for Payload in Payloads
    }
    if (KPartitionStream, "deltas") not in StreamsValue:
        raise ValueError("local body rollback history is missing")
    if len(Payloads) != 3 or StreamsValue.keys() != {
        (KLocalBodyStream, "unknown"),
        (KPartitionStream, "partition"),
        (KPartitionStream, "deltas"),
    }:
        raise ValueError("local body requires the sole selected payload group")
    LocalData = StreamsValue[(KLocalBodyStream, "unknown")]
    ActiveData = StreamsValue[(KPartitionStream, "partition")]
    HistoryData = StreamsValue[(KPartitionStream, "deltas")]
    if LocalData is None or ActiveData is None or HistoryData is None:
        raise ValueError("local body payload group is incomplete")
    ActiveNodes = ReadActiveNodes(ActiveData)
    CheckXmtGraph(ActiveNodes)
    if len(ActiveNodes) != 1 or ActiveNodes[1].Integer("body"):
        raise ValueError("local body requires an empty active partition")
    ReadXmtHistory(HistoryData, ActiveNodes)
    return LocalData
