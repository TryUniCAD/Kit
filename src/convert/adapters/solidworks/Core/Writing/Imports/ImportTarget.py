from dataclasses import replace as ReplaceValue
from os import name as OsName
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.StageFileScope import GetStagedFinal
from interchange.Core.Common import FreezeMapping


# the claimed self locator cannot detach a physical part write from its actual final destination
def ImportTarget(
    TargetValue: KTargetType,
    SettingsValue: WriteOptions,
) -> tuple[FilePath | None, WriteOptions]:
    if not isinstance(TargetValue, (str, FilePath)):
        return None, SettingsValue
    OutputPath = FilePath(TargetValue).expanduser().resolve()
    FinalPath = GetStagedFinal(OutputPath)
    Requested = SettingsValue.values.get("final_destination", FinalPath)
    if (
        OsName != "nt"
        or not isinstance(Requested, (str, FilePath))
        or str(Requested) != str(FinalPath)
        or OutputPath.name != FinalPath.name
    ):
        raise ValueError("local solid needs its actual measured Windows destination")
    return OutputPath, ReplaceValue(
        SettingsValue,
        values=FreezeMapping(
            dict(SettingsValue.values) | {"final_destination": str(FinalPath)}
        ),
    )
