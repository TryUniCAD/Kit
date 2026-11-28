from os import name as OsName
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.StageFileScope import GetStagedFinal
from convert.Security.PathBoundary import ResolveWithin


# the measured path must belong to the actual windows target or its scoped registry staging entry
def CheckThinPath(
    TargetValue: KTargetType, OptionsValue: WriteOptions, Locator: str
) -> FilePath | None:
    Requested = OptionsValue.values.get("final_destination")
    if not isinstance(TargetValue, (str, FilePath)):
        if Requested != Locator:
            raise ValueError(
                "measured thin revolve stream requires its exact inspected self locator"
            )
        return None
    if OsName != "nt":
        raise ValueError(
            "measured thin revolve filesystem output requires its inspected Windows path"
        )
    TargetPath = FilePath(TargetValue).expanduser().absolute()
    OutputPath = ResolveWithin(TargetPath.name, TargetPath.parent)
    ActualPath = GetStagedFinal(OutputPath)
    NativePath = FilePath(PureWindowsPath(Locator))
    if (
        TargetPath.name != NativePath.name
        or OutputPath.name != NativePath.name
        or ActualPath != NativePath
        or Requested not in (None, Locator, str(ActualPath))
    ):
        raise ValueError(
            "measured thin revolve filesystem destination differs from its inspected locator"
        )
    return OutputPath
