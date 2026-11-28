from os import name as OsName
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.StageFileScope import GetStagedFinal


# a path must be the real measured destination and a stream must carry its exact locator
def StockTarget(
    TargetValue: KTargetType, OptionsValue: WriteOptions, LocatorValue: str
) -> FilePath | None:
    FinalValue = OptionsValue.values.get("final_destination")
    if isinstance(TargetValue, (str, FilePath)):
        StagePath = FilePath(TargetValue).expanduser().resolve()
        ActualPath = GetStagedFinal(StagePath)
        if (
            OsName != "nt"
            or str(ActualPath) != LocatorValue
            or StagePath.name != PureWindowsPath(LocatorValue).name
            or (
                FinalValue is not None
                and (
                    not isinstance(FinalValue, (str, FilePath))
                    or FilePath(FinalValue).expanduser().resolve() != ActualPath
                )
            )
        ):
            raise ValueError("selected stock requires its actual measured final path")
        return StagePath
    if (
        not IsBinaryTarget(TargetValue)
        or type(FinalValue) is not str
        or FinalValue != LocatorValue
    ):
        raise ValueError("selected stock stream requires its exact measured locator")
    return None
