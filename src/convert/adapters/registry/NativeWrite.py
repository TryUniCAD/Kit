from convert.adapters.base.Materials.CheckMatState import CheckMatState
from convert.adapters.registry.NativeHistory import CheckHistory
from convert.adapters.registry.NativeReadOnly import CheckReadOnly
from interchange.document.Models.DocumentModel import CadDocument


# direct writers require both native history qualification and inspection export restrictions
def CheckNative(Document: CadDocument) -> None:
    CheckMatState(Document)
    CheckHistory(Document)
    CheckReadOnly(Document)
