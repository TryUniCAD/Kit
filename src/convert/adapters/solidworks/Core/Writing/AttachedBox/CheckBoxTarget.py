from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxMeasure import BoxMeasure
from convert.adapters.solidworks.Core.Writing.Measured.MatchMeasPath import MatchMeasPath


# only a real final native path or an explicitly named standalone binary stream can be measured
def CheckBoxTarget(
    TargetValue: KTargetType, MeasureValue: BoxMeasure
) -> FilePath | None:
    Settings = MeasureValue.SettingsValue
    FinalValue = Settings.values.get("final_destination")
    Locator = MeasureValue.NativePath
    if isinstance(TargetValue, (str, FilePath)):
        return MatchMeasPath(
            TargetValue,
            FinalValue,
            Locator,
            "measured attached box requires its actual final native locator",
        )
    if not IsBinaryTarget(TargetValue) or FinalValue != Locator:
        raise ValueError(
            "measured attached box stream requires its exact native locator"
        )
    return None
