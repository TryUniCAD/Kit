from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.Materials.CheckMatState import CheckMatState
from convert.adapters.registry.NativeHistory import CheckHistory
from convert.adapters.registry.NativeReadOnly import CheckReadOnly
from interchange.document.Models.DocumentModel import CadDocument


# direct writers require both native history qualification and inspection export restrictions
def CheckNative(
    Document: CadDocument,
    WriterValue: object = None,
    TargetValue: KTargetType | None = None,
) -> None:
    CheckMatState(Document)
    CheckHistory(Document, WriterValue, TargetValue)
    CheckReadOnly(Document)
