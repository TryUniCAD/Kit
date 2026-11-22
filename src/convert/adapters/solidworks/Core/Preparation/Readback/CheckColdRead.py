from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdPart import (
    ReadColdPart,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# comparison covers every derived and retained field without making it an input to generation
def CheckColdRead(Document: CadDocument, Payload: bytes) -> None:
    Expected = ReadColdPart(Payload, Document.source.path, ReadOptions())
    if Expected.brep is None or ToJson(Document, IndentSize=None) != ToJson(
        Expected, IndentSize=None
    ):
        raise ValueError("SOLIDWORKS cold readback differs from its regenerated part")
