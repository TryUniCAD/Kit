from os import name as OsName
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# selection rejects unsupported neutral boundaries before a staged destination is opened
def CanImportBox(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    if isinstance(TargetValue, (str, FilePath)):
        PathValue = FilePath(TargetValue)
        if (
            OsName != "nt"
            or PathValue.suffix.casefold() != KPartSuffix
            or PathValue.is_dir()
        ):
            return False
        NameValue = PathValue.stem
    elif IsBinaryTarget(TargetValue):
        NameValue = "Imported geometry"
    else:
        return False
    try:
        _ = PlanImportPart(DocumentValue, NameValue)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    return True
