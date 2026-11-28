from os import name as OsName
from pathlib import Path as FilePath, PureWindowsPath
from sys import platform as PlatformName

from convert.Security.PathBoundary import ResolveWithin, UnsafePath
from convert.adapters.Staging.StageFileScope import GetStagedFinal


# the inspected share name identifies the actual host path for profiles measured on that share
def MeasDiskPath(Locator: str, FailureText: str, AllowMacHome: bool) -> FilePath:
    if OsName == "nt":
        return FilePath(Locator)
    NativePath = PureWindowsPath(Locator)
    if AllowMacHome and PlatformName == "darwin" and NativePath.drive.casefold() == r"\\mac\home":
        return FilePath.home().joinpath(*NativePath.parts[1:])
    raise ValueError(FailureText)


# physical publication binds the requested file and its actual registry staging entry
def MatchMeasPath(
    TargetValue: str | FilePath,
    FinalValue: object,
    Locator: str,
    FailureText: str,
    *,
    AllowMacHome: bool = False,
) -> FilePath:
    NativePath = MeasDiskPath(Locator, FailureText, AllowMacHome)
    Expected = Locator if OsName == "nt" else str(NativePath)
    if AllowMacHome and type(FinalValue) is str and FinalValue == Locator:
        FinalValue = None
    try:
        StagePath = ResolveWithin(FilePath(TargetValue).expanduser().absolute(), NativePath.parent)
        Physical = GetStagedFinal(StagePath)
        if (
            str(Physical) != Expected
            or StagePath.name != NativePath.name
            or (
                FinalValue is not None
                and (
                    not isinstance(FinalValue, (str, FilePath))
                    or ResolveWithin(FilePath(FinalValue).expanduser().absolute(), NativePath.parent) != Physical
                )
            )
        ):
            raise ValueError(FailureText)
    except (UnsafePath, FileNotFoundError) as ErrorValue:
        raise ValueError(FailureText) from ErrorValue
    return StagePath
