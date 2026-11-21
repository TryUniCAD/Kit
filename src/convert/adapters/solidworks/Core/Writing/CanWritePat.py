from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Core.Preparation.Patterns.PrepPatPart import (
    PrepPatPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# a stream probe has no options yet while a path probe can validate the actual basename and locator
def CanWritePat(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        if isinstance(TargetValue, (str, FilePath)):
            OutputPath = FilePath(TargetValue).expanduser().resolve()
        elif IsBinaryTarget(TargetValue):
            OutputPath = None
        else:
            return False
        _ = PrepPatPart(DocumentValue, OutputPath, 1)
    except (OSError, TypeError, ValueError):
        return False
    return True
