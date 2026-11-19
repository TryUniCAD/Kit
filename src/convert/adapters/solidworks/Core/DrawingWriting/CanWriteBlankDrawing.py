from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.DrawingWriting.BlankTargetName import (
    BlankTargetName,
)
from convert.adapters.solidworks.Core.DrawingWriting.NeedBlankDrawing import (
    NeedBlankDrawing,
)
from interchange.document.Models.DocumentModel import CadDocument


# unsupported drawing intent should leave the registry before it creates a staging destination
def CanWriteBlankDrawing(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        _ = BlankTargetName(DocumentValue, TargetValue)
        _ = NeedBlankDrawing(DocumentValue)
    except (TypeError, ValueError):
        return False
    return True
