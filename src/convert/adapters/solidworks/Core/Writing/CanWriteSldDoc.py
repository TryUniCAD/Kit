from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.AssemblyWriting.CanWriteAsm import CanWriteAsm
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.CanWriteNested import (
    CanWriteNested,
)
from convert.adapters.solidworks.Core.DrawingWriting.CanWriteBlankDrawing import (
    CanWriteBlank,
)
from convert.adapters.solidworks.Core.Writing.CanWritePart import CanWritePart
from interchange.document.Models.DocumentModel import CadDocument


# selection must retain the exact independent assembly drawing and part admission boundaries
def CanWriteSldDoc(Document: CadDocument, Target: KTargetType) -> bool:
    if Document.DrawingValue is not None:
        return CanWriteBlank(Document, Target)
    if Document.assembly is not None:
        return CanWriteNested(Document, Target) or CanWriteAsm(Document, Target)
    return CanWritePart(Document, Target)
