from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import ReadNativePart, SldprtAdapter
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# full readback equality guards every additional source domain before any bytes can be published
def CheckPatRead(Document: CadDocument, Payload: bytes) -> None:
    SourceName = Document.source.path
    Expected = ReadNativePart(
        SldprtAdapter(),
        SldprtArchive.from_bytes(Payload, SourceName),
        Payload,
        SourceName,
        ReadOptions(),
    )
    if Expected.brep is None or ToJson(Document, IndentSize=None) != ToJson(
        Expected, IndentSize=None
    ):
        raise ValueError(
            "SOLIDWORKS cold pattern readback differs from its regenerated part"
        )
