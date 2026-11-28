from pathlib import Path as FilePath

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import (
    MatchMeasPath,
)


# the measured native hierarchy is usable only where its encoded siblings actually reside
def IsNestSite(
    StagePath: FilePath, FinalPath: FilePath, NativePath: str, Settings: WriteOptions
) -> bool:
    try:
        _ = MatchMeasPath(
            StagePath,
            FinalPath,
            NativePath,
            "nested publication requires the measured physical locator",
            AllowMacHome=True,
        )
    except ValueError:
        RequireAsm(
            Settings.values.get("defer_native_delivery") is True
            and Settings.values.get("allow_carrier") is True
            and "native_destination" in Settings.values,
            "nested bundle requires its measured location or explicit deferred delivery",
        )
        return False
    return True
