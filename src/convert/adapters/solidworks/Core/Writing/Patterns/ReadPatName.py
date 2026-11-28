from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.WriteOptions import WriteOptions


# the exact measured full file digest also binds the resolved authored basename
def ReadPatName(SettingsValue: WriteOptions, OutputPath: FilePath | None) -> str:
    PathValue = SettingsValue.values.get("final_destination", OutputPath)
    if not isinstance(PathValue, (str, FilePath)):
        raise ValueError("SOLIDWORKS cold pattern needs an explicit final destination")
    return PureWindowsPath(PathValue).stem
