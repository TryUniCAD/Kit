from collections.abc import Mapping

from convert.Geometry.Parasolid import DecodeBrepModel
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyKernel import (
    ReadBodyKernel,
)
from interchange.document.Models.DocumentModel import CadDocument


# public geometry must come from the selected live partition rather than another readable cache
def ReadBodyCache(
    Document: CadDocument, Archive: SldprtArchive, StreamName: str
) -> tuple[Mapping[int, XmtNode], tuple[int, int]]:
    Payloads, NodesValue, MarksValue = ReadBodyKernel(
        Archive.require(StreamName), StreamName
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
    return NodesValue, MarksValue
