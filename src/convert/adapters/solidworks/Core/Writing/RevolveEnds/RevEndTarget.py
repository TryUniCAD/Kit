from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import (
    MatchMeasPath,
)


# the full file digest qualifies only the exact measured self path or an empty named stream
def RevEndTarget(
    TargetValue: KTargetType, Settings: WriteOptions, LocatorValue: str
) -> FilePath | None:
    FinalValue = Settings.values.get("final_destination")
    if isinstance(TargetValue, (str, FilePath)):
        return MatchMeasPath(
            TargetValue,
            FinalValue,
            LocatorValue,
            "measured revolve filesystem destination differs from its inspected locator",
            AllowMacHome=True,
        )
    if (
        not IsBinaryTarget(TargetValue)
        or type(FinalValue) is not str
        or FinalValue != LocatorValue
    ):
        raise ValueError(
            "measured revolve stream needs its exact inspected self locator"
        )
    return None
