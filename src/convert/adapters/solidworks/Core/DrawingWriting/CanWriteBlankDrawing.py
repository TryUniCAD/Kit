from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Core.DrawingWriting.BlankTargetName import (
    BlankTargetName,
)
from convert.adapters.solidworks.Core.DrawingWriting.NeedBlankDrawing import (
    NeedBlankDraw,
)
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.NeedRewrite import (
    NeedRewrite,
)
from interchange.document.Models.DocumentModel import CadDocument


# unsupported drawing intent should leave the registry before it creates a staging destination
def CanWriteBlank(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        if "solidworks.blank.profile" in DocumentValue.source.attributes:
            _ = NeedRewrite(DocumentValue, TargetValue)
        else:
            _ = BlankTargetName(DocumentValue, TargetValue)
            _ = NeedBlankDraw(DocumentValue)
    except (TypeError, ValueError):
        return False
    return True
