from pathlib import Path as FilePath

from convert.adapters.solidworks.Core.AssemblyWriting.CheckFreshFiles import (
    CheckFreshFiles,
)


# the existing flat profile owns exactly one generated part beside its parent
def CheckFreshAsm(TargetValue: FilePath, ChildName: str) -> None:
    CheckFreshFiles(TargetValue, (ChildName + ".SLDPRT",))
