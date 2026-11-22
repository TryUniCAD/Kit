from os import name as OsName
from pathlib import Path as FilePath

from convert.Security.PathBoundary import ResolveWithin, UnsafePath
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.StageFileScope import GetStagedFinal


# an actual path or its registry staging entry must have the measured windows destination
def StockFilePath(
    TargetValue: str | FilePath, FinalValue: object, Locator: str
) -> FilePath:
    PathError = "selected stock requires its actual measured final path"
    if OsName != "nt":
        raise ValueError(PathError)
    NativePath = FilePath(Locator)
    try:
        StagePath = ResolveWithin(
            FilePath(TargetValue).expanduser().absolute(), NativePath.parent
        )
        Physical = GetStagedFinal(StagePath)
        if (
            str(Physical) != Locator
            or StagePath.name != NativePath.name
            or (
                FinalValue is not None
                and (
                    not isinstance(FinalValue, (str, FilePath))
                    or ResolveWithin(
                        FilePath(FinalValue).expanduser().absolute(), NativePath.parent
                    )
                    != Physical
                )
            )
        ):
            raise ValueError(PathError)
    except (UnsafePath, FileNotFoundError) as ErrorValue:
        raise ValueError(PathError) from ErrorValue
    return StagePath


# a named standalone stream must retain the exact locator already measured by the native observer
def StockTarget(
    TargetValue: KTargetType, OptionsValue: WriteOptions, LocatorValue: str
) -> FilePath | None:
    FinalValue = OptionsValue.values.get("final_destination")
    if isinstance(TargetValue, (str, FilePath)):
        return StockFilePath(TargetValue, FinalValue, LocatorValue)
    if (
        not IsBinaryTarget(TargetValue)
        or type(FinalValue) is not str
        or FinalValue != LocatorValue
    ):
        raise ValueError("selected stock stream requires its exact measured locator")
    return None
