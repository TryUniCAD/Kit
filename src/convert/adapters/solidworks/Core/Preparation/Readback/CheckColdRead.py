from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdDoc import (
    ReadColdDoc,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# comparison covers every derived and retained field without making it an input to generation
def CheckColdRead(Document: CadDocument, Payload: bytes) -> None:
    Expected = ReadColdDoc(Document.source.path, Payload)
    if Expected.brep is None or ToJson(Document, IndentSize=None) != ToJson(
        Expected, IndentSize=None
    ):
        raise ValueError("SOLIDWORKS cold readback differs from its regenerated part")
