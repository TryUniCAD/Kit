from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Writing.AttachedBox.ProveBoxSource import (
    ProveBoxSource,
)
from interchange.document.Models.DocumentModel import CadDocument


# format selection must recognize an intact verified source before choosing a publication path
def CanWriteBox(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    ProofValue = ProveBoxSource(DocumentValue)
    if not isinstance(TargetValue, (str, FilePath)):
        return IsBinaryTarget(TargetValue)
    TargetPath = FilePath(TargetValue)
    NameValue = ProofValue.PlanValue.PartSource.ModelValue.metadata.get("name")
    return (
        TargetPath.stem == NameValue
        and TargetPath.suffix.casefold() == KPartSuffix
        and not TargetPath.is_dir()
    )
