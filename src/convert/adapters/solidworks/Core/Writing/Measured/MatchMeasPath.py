from os import name as OsName
from pathlib import Path as FilePath

from convert.Security.PathBoundary import ResolveWithin, UnsafePath
from convert.adapters.Staging.StageFileScope import GetStagedFinal


# physical publication binds the requested file and its actual registry staging entry
def MatchMeasPath(
    TargetValue: str | FilePath, FinalValue: object, Locator: str, FailureText: str
) -> FilePath:
    if OsName != "nt":
        raise ValueError(FailureText)
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
            raise ValueError(FailureText)
    except (UnsafePath, FileNotFoundError) as ErrorValue:
        raise ValueError(FailureText) from ErrorValue
    return StagePath
