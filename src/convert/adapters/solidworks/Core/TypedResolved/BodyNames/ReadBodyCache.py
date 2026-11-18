from collections.abc import Mapping

from convert.Geometry.Parasolid import DecodeBrepModel, DecodePartData
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtHistory import ReadXmtHistory
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Models.DocumentModel import CadDocument


# public geometry must come from the selected live partition rather than another readable cache
def ReadBodyCache(
    Document: CadDocument, Archive: SldprtArchive, StreamName: str
) -> Mapping[int, XmtNode]:
    StreamValue = Archive.require(StreamName)
    Payloads = DecodePartData(StreamValue, StreamName)
    if tuple(Payload.kind for Payload in Payloads) != ("partition", "deltas") or any(
        Payload.schema != "SCH_3701250_37102_13006" for Payload in Payloads
    ):
        raise ValueError(
            "selected body cache is not the witnessed active and rollback profile"
        )
    ActivePayload = Payloads[0]
    Attached = tuple(
        Payload
        for Payload in Document.brep_payloads
        if Payload.source_stream == StreamName and Payload.kind == "partition"
    )
    if (
        len(Attached) != 1
        or Attached[0].data != ActivePayload.data
        or Attached[0].sha256 != ActivePayload.sha256
    ):
        raise ValueError("public body has no exact selected native payload")
    DecodedValue = DecodeBrepModel(ActivePayload.data)
    if DecodedValue is None or DecodedValue != Document.brep:
        raise ValueError("public geometry does not match the selected native partition")
    NodesValue = ReadActiveNodes(ActivePayload.data)
    CheckXmtGraph(NodesValue)
    ReadXmtHistory(Payloads[1].data, NodesValue)
    return NodesValue
