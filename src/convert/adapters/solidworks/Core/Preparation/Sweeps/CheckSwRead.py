from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwDoc import MakeSwDoc
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwPart import SwSource
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwState import (
    ReadSwState,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# readback publication must account for every field of the exact canonical original projection
def CheckSwRead(DocumentValue: CadDocument, Payload: bytes) -> None:
    Label = DocumentValue.source.path
    StateValue = ReadSwState(SldprtArchive.from_bytes(Payload, Label))
    SourceValue = SwSource(StateValue, Payload, Label)
    Expected = MakeSwDoc(StateValue, SourceValue, DocumentValue.brep is not None)
    if ToJson(Expected, IndentSize=None) != ToJson(DocumentValue, IndentSize=None):
        raise ValueError(
            "SOLIDWORKS cold sweep readback differs from its regenerated part"
        )
