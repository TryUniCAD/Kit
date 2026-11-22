from os import fspath as PathText
from os import name as OsName
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.CheckNativePath import (
    CheckNativePath,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm


# native windows destinations establish linked identity directly while other host paths require an explicit caller mapping
def FinalAsmPath(
    TargetValue: FilePath, SettingsValue: WriteOptions
) -> tuple[FilePath, str]:
    FinalValue = SettingsValue.values.get("final_destination", TargetValue)
    RequireAsm(
        isinstance(FinalValue, (str, FilePath)),
        "assembly final destination requires a filesystem path",
    )
    if not isinstance(FinalValue, (str, FilePath)):
        raise TypeError("assembly final destination requires a filesystem path")
    FinalText = PathText(FinalValue)
    FinalPath = FilePath(FinalText).expanduser().resolve()
    NativeValue = SettingsValue.values.get("native_destination")
    if NativeValue is None:
        RequireAsm(
            FilePath(FinalText).is_absolute()
            and PureWindowsPath(FinalText).is_absolute(),
            "cross-host assembly output requires explicit native_destination",
        )
        NativeValue = FinalText
    if not isinstance(NativeValue, (str, FilePath)):
        raise TypeError("assembly native destination requires explicit path text")
    NativeText = PathText(NativeValue)
    NativePath = CheckNativePath(NativeText)
    if OsName == "nt":
        RequireAsm(
            NativePath == PureWindowsPath(FinalPath),
            "native assembly locator must match the final Windows destination",
        )
    RequireAsm(
        TargetValue.name == FinalPath.name == NativePath.name,
        "staged final and native assembly filenames must agree",
    )
    return FinalPath, NativeText
