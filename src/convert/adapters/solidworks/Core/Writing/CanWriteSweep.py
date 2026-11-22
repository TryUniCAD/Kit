from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.Sweeps.PlanSwTarget import (
    PlanSwTarget,
)
from interchange.document.Models.DocumentModel import CadDocument


# stream discovery uses a neutral locator until the caller supplies the final destination
def CanWriteSweep(DocumentValue: CadDocument, TargetValue: KTargetType) -> bool:
    try:
        if isinstance(TargetValue, (str, FilePath)):
            OutputPath = FilePath(TargetValue).expanduser().resolve()
            if not PureWindowsPath(str(OutputPath)).drive or OutputPath.is_dir():
                return False
        elif IsBinaryTarget(TargetValue):
            OutputPath = None
        else:
            return False
        _ = PlanSwTarget(DocumentValue, OutputPath, 1, WriteOptions())
    except (OSError, TypeError, ValueError):
        return False
    return True
