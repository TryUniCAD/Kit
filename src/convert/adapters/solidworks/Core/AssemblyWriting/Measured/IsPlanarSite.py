from pathlib import Path as FilePath

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import (
    MatchMeasPath,
)


# physical relocation may stage the exact native bundle but cannot inherit its native evidence at a different location
def IsPlanarSite(
    StagePath: FilePath, FinalPath: FilePath, NativePath: str, Settings: WriteOptions
) -> bool:
    try:
        _ = MatchMeasPath(
            StagePath,
            FinalPath,
            NativePath,
            "assembly publication requires the measured physical locator",
            AllowMacHome=True,
        )
    except ValueError:
        RequireAsm(
            Settings.values.get("defer_native_delivery") is True
            and Settings.values.get("allow_carrier") is True
            and "native_destination" in Settings.values,
            "planar bundle requires its measured location or explicit deferred delivery",
        )
        return False
    return True
