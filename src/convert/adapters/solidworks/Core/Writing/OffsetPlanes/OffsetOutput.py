from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import (
    MatchMeasPath,
)


# output must preserve the authored windows self locator across standalone streams and real staging paths
def OffsetOutput(
    TargetValue: KTargetType, Settings: WriteOptions, Locator: str
) -> tuple[FilePath | None, WriteOptions]:
    Requested = Settings.values.get("final_destination")
    OutputPath: FilePath | None = None
    if isinstance(TargetValue, (str, FilePath)):
        OutputPath = MatchMeasPath(
            TargetValue,
            Requested,
            Locator,
            "measured offset filesystem destination differs from its authored locator",
            AllowMacHome=True,
        )
    elif (
        not IsBinaryTarget(TargetValue)
        or type(Requested) is not str
        or Requested != Locator
    ):
        raise ValueError("measured offset stream requires its exact authored locator")
    return OutputPath, ReplaceValue(
        Settings, values={**Settings.values, "final_destination": Locator}
    )
