from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Container.Format import KAsmSuffix
from convert.adapters.solidworks.Core.AssemblyPreparation.Nested.ReadNestedAssembly import (
    ReadNestedAssembly,
)
from interchange.document.Models.DocumentModel import CadDocument


# selection qualifies only the complete nested graph and its named assembly destination
def CanWriteNested(Document: CadDocument, TargetValue: KTargetType) -> bool:
    if not isinstance(TargetValue, (str, FilePath)):
        return False
    OutputPath = FilePath(TargetValue)
    if OutputPath.suffix.casefold() != KAsmSuffix:
        return False
    try:
        PlanValue = ReadNestedAssembly(Document)
    except (TypeError, ValueError):
        return False
    return OutputPath.stem == PlanValue.RootValue.name
