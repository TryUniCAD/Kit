from ntpath import join as JoinPath
from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import IsDeviceName
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.Preparation.SelectPartSelf import KNeutralRoot


# a standalone blank drawing needs a native locator when the host has no windows drive mapping
def BlankSelfFile(TargetValue: FilePath, FinalValue: object, WrittenAt: int) -> SelfFileInput:
    Destination = TargetValue if FinalValue is None else FinalValue
    if not isinstance(Destination, (str, FilePath)):
        raise TypeError("final drawing destination requires a filesystem path")
    FinalPath = FilePath(Destination)
    if not FinalPath.is_absolute() or FinalPath.name != TargetValue.name:
        raise ValueError("staged and final drawing filenames must agree")
    NativePath = PureWindowsPath(str(FinalPath))
    if not NativePath.drive:
        return SelfFileInput(JoinPath(KNeutralRoot, FinalPath.name), WrittenAt)
    if (
        str(NativePath).startswith(("\\\\?\\", "\\\\.\\"))
        or ".." in NativePath.parts
        or any(
            IsDeviceName(PartValue)
            or PartValue.endswith((".", " "))
            or any(ord(Character) < 32 or Character in '<>:"|?*' for Character in PartValue)
            for PartValue in NativePath.parts[1:]
        )
    ):
        raise ValueError("native drawing requires an ordinary Windows destination")
    return SelfFileInput(str(NativePath), WrittenAt)
