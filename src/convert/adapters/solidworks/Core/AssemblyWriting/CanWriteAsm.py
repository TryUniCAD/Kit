from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Container.Format import KAsmSuffix
from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import (
    CheckAsmShape,
)
from interchange.document.Models.DocumentModel import CadDocument


# selection must admit only named filesystem assembly bundles whose complete ordinary neutral profile can be projected
def CanWriteAsm(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    if not isinstance(TargetValue, (str, FilePath)):
        return False
    OutputPath = FilePath(TargetValue)
    if OutputPath.suffix.casefold() != KAsmSuffix:
        return False
    try:
        NameValue = CheckAsmShape(DocumentValue)
    except (TypeError, ValueError):
        return False
    return OutputPath.stem == NameValue
