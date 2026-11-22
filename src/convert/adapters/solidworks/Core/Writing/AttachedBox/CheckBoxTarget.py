from os import name as OsName
from pathlib import Path as FilePath

from convert.Security.PathBoundary import ResolveWithin, UnsafePath
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxMeasure import BoxMeasure
from convert.adapters.Staging.StageFileScope import GetStagedFinal


# only a real final native path or an explicitly named standalone binary stream can be measured
def CheckBoxTarget(
    TargetValue: KTargetType, MeasureValue: BoxMeasure
) -> FilePath | None:
    Settings = MeasureValue.SettingsValue
    FinalValue = Settings.values.get("final_destination")
    Locator = MeasureValue.NativePath
    if isinstance(TargetValue, (str, FilePath)):
        PathError = "measured attached box requires its actual final native locator"
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
                            FilePath(FinalValue).expanduser().absolute(),
                            NativePath.parent,
                        )
                        != Physical
                    )
                )
            ):
                raise ValueError(PathError)
        except UnsafePath as ErrorValue:
            raise ValueError(PathError) from ErrorValue
        return StagePath
    if not IsBinaryTarget(TargetValue) or FinalValue != Locator:
        raise ValueError(
            "measured attached box stream requires its exact native locator"
        )
    return None
