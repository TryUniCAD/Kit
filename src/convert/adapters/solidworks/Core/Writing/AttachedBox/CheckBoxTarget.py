from os import name as OsName
from pathlib import Path as FilePath
from pathlib import PureWindowsPath

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
    NativePath = PureWindowsPath(Locator)
    if isinstance(TargetValue, (str, FilePath)):
        StagePath = FilePath(TargetValue).expanduser().resolve()
        Physical = GetStagedFinal(StagePath)
        if (
            OsName != "nt"
            or str(Physical) != Locator
            or StagePath.name != NativePath.name
            or (FinalValue is not None and not isinstance(FinalValue, (str, FilePath)))
            or (
                isinstance(FinalValue, (str, FilePath))
                and FilePath(FinalValue).expanduser().resolve() != Physical
            )
        ):
            raise ValueError(
                "measured attached box requires its actual final native locator"
            )
        return StagePath
    if not IsBinaryTarget(TargetValue) or FinalValue != Locator:
        raise ValueError(
            "measured attached box stream requires its exact native locator"
        )
    return None
