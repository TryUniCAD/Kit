from os import name as OsName
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# physical imports need an actual windows locator and all imports need a validated local boundary
def CanImportPart(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    if isinstance(TargetValue, (str, FilePath)):
        PathValue = FilePath(TargetValue)
        if (
            OsName != "nt"
            or PathValue.suffix.casefold() != KPartSuffix
            or PathValue.is_dir()
        ):
            return False
        LocatorValue = str(PathValue)
    elif IsBinaryTarget(TargetValue):
        LocatorValue = "Imported geometry" + KPartSuffix
    else:
        return False
    try:
        _ = PlanImportPart(DocumentValue, LocatorValue)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    return True
