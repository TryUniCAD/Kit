from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# comparison covers every derived and retained field without making it an input to generation
def CheckColdRead(Document: CadDocument, Payload: bytes) -> None:
    from convert.adapters.solidworks.Core.Adapter import ReadNativePart, SldprtAdapter

    SourceName = Document.source.path
    Archive = SldprtArchive.from_bytes(Payload, SourceName)
    Expected = ReadNativePart(
        SldprtAdapter(),
        Archive,
        Payload,
        SourceName,
        ReadOptions(),
    )
    if Expected.brep is None or ToJson(Document, IndentSize=None) != ToJson(
        Expected, IndentSize=None
    ):
        raise ValueError("SOLIDWORKS cold readback differs from its regenerated part")
