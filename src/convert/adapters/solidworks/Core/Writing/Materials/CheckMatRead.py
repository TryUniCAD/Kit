from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Materials.Cold.ReadMatLane import (
    ReadMatLane,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# an exact measured publication must still represent the complete supplied cold material design
def CheckMatRead(DocumentValue: CadDocument, Payload: bytes) -> None:
    Label = DocumentValue.source.path
    Archive = SldprtArchive.from_bytes(Payload, Label)
    Expected = ReadMatLane(
        Archive,
        Payload,
        Label,
        ReadOptions(include_brep=DocumentValue.brep is not None),
    )
    if Expected is None or ToJson(DocumentValue, IndentSize=None) != ToJson(
        Expected, IndentSize=None
    ):
        raise ValueError("cold material readback differs from the regenerated part")
