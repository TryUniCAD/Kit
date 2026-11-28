from datetime import datetime as DateTime, timedelta as TimeDelta, timezone as TimeZone
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.AsmInfoInput import (
    AsmInfoInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.InfoLocalDate import (
    InfoLocalDate,
    InfoLocalTime,
)
from convert.adapters.solidworks.Container.Format import KAsmSuffix


# the system table keeps filename root title and core provenance independent even on the first publication
def InfoDocValues(
    FilePath: str,
    HeaderPath: str,
    ModelTitle: str,
    ConfigName: str,
    SavedAt: int,
    InputValue: AsmInfoInput,
) -> dict[str, str | int | bool]:
    PathValue = PureWindowsPath(FilePath)
    if PathValue.suffix.casefold() != KAsmSuffix or not PathValue.stem:
        raise ValueError("assembly information needs its actual output filename")
    if type(SavedAt) is not int or not InputValue.CreatedAt <= SavedAt <= 0xFFFFFFFF:
        raise ValueError(
            "assembly information save must follow its actual core creation"
        )
    ZoneValue = TimeZone(TimeDelta(minutes=InputValue.OffsetMinutes))
    CreatedValue = DateTime.fromtimestamp(InputValue.CreatedAt, ZoneValue)
    SavedValue = DateTime.fromtimestamp(SavedAt, ZoneValue)
    FolderValue = (
        str(PureWindowsPath(HeaderPath).parent).rstrip("\\") + "\\"
        if HeaderPath
        else ""
    )
    return {
        "SW-File Name": PathValue.stem,
        "SW-BOM Part Number": ModelTitle,
        "SW-Folder Name": FolderValue,
        "SW-Short Date": f"{SavedValue.month:02d}/{SavedValue.day:02d}/{SavedValue.year:04d}",
        "SW-Long Date": InfoLocalDate(SavedValue),
        "SW-Configuration Name": ConfigName,
        "SW-Author": "",
        "SW-Keywords": "",
        "SW-Comments": "",
        "SW-Title": "",
        "SW-Subject": "",
        "SW-Created Date": InfoLocalTime(CreatedValue),
        "SW-Last Saved Date": InfoLocalTime(SavedValue),
        "SW-Last Saved By": InputValue.SaveActor,
        "SW-File Title": "",
        "V_WorldOrientation": 1,
        "Assembly type": False,
        "SW-HasDesignTable": 0,
        "IsCPReArchEnabled": 1,
        "Component Type": 0,
    }
