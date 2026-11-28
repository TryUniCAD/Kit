from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.Security.PathBoundary import ResolveWithin
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.StageFileScope import GetStagedFinal
from interchange.Core.Common import FreezeMapping


# a real output path must use the direct destination or its actual registry transaction owner
def CircOutput(
    TargetValue: KTargetType, Settings: WriteOptions
) -> tuple[FilePath | None, WriteOptions]:
    if not isinstance(TargetValue, (str, FilePath)):
        return None, Settings
    Requested = FilePath(TargetValue).expanduser().absolute()
    OutputPath = ResolveWithin(Requested.name, Requested.parent)
    Actual = GetStagedFinal(OutputPath)
    Intent = Settings.values.get("final_destination")
    if Intent is not None and Intent != str(Actual):
        raise ValueError("measured circle requires its actual final filesystem locator")
    return OutputPath, ReplaceValue(
        Settings,
        values=FreezeMapping({**Settings.values, "final_destination": str(Actual)}),
    )
