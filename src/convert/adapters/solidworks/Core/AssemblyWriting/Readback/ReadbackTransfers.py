from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WritePolicy import GetDocumentCaps
from interchange.document.Models.DocumentModel import CadDocument


# the full regenerated reader model verifies each preserved capability before final writes
def ReadbackTrans(Document: CadDocument) -> tuple[CapTransfer, ...]:
    return tuple(
        CapTransfer(Value, TransferMode.KNative)
        for Value in sorted(GetDocumentCaps(Document))
    )
