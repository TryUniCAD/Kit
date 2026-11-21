from collections.abc import Sequence

from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from interchange.Payloads.PayloadRecord import BrepPayload


# both readback paths need the same exact configuration payload selection
def ReadLocalState(
    Payloads: Sequence[BrepPayload], PartitionData: bytes | None = None
) -> tuple[bytes, int, int]:
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
    if PartitionData is not None:
        Actual = DecodePartData(PartitionData, KPartitionStream)
        if tuple((Payload.kind, Payload.data) for Payload in Actual) != (
            ("partition", ActiveData),
            ("deltas", HistoryData),
        ):
            raise ValueError("local body selection differs from the archive partition")
    ActiveNodes = ReadActiveNodes(ActiveData)
    CheckXmtGraph(ActiveNodes)
    if len(ActiveNodes) != 1 or ActiveNodes[1].Integer("body"):
        raise ValueError("local body requires an empty active partition")
    _, PriorMark = ReadHistMarks(HistoryData, ActiveNodes)
    return LocalData, ActiveNodes[1].Integer("current_id"), PriorMark


# callers without activation ownership keep the selected body and mark interface
def ReadLocalPay(
    Payloads: Sequence[BrepPayload], PartitionData: bytes | None = None
) -> tuple[bytes, int]:
    LocalData, MarkValue, _ = ReadLocalState(Payloads, PartitionData)
    return LocalData, MarkValue
