from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import (
    MatchMeasPath,
)
from interchange.Core.Common import FreezeMapping


# the exact encoded self locator must agree with the real staged file or requested standalone stream
def ReadRevTarget(
    TargetValue: KTargetType, Settings: WriteOptions, Locator: str
) -> tuple[FilePath | None, WriteOptions]:
    Requested = Settings.values.get("final_destination")
    if isinstance(TargetValue, (str, FilePath)):
        OutputPath = MatchMeasPath(
            TargetValue,
            Requested,
            Locator,
            "measured revolve filesystem destination differs from its inspected locator",
            AllowMacHome=True,
        )
    else:
        OutputPath = None
        if type(Requested) is not str or Requested != Locator:
            raise ValueError("measured revolve stream requires its exact inspected self locator")
    return OutputPath, ReplaceValue(
        Settings,
        values=FreezeMapping(dict(Settings.values) | {"final_destination": Locator}),
    )
