from pathlib import PureWindowsPath
from convert.adapters.base.ContractTypes import IsDeviceName
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Container.Format import (
    KPartSuffix,
)


# self identity must preserve a real explicit windows part path without guessing host drive mappings or consulting filesystem state
def RequirePartPath(PathText: str, SavedAt: int) -> SelfFileInput:
    InputValue = SelfFileInput(PathText, SavedAt)
    PathValue = PureWindowsPath(PathText)
    if PathValue.suffix.casefold() != KPartSuffix:
        raise ValueError("plain part preparation cannot target an assembly or drawing")
    if (
        PathText.startswith(("\\\\?\\", "\\\\.\\"))
        or any(ord(Character) < 32 for Character in PathText)
        or any(
            Value in (".", "..") for Value in PathText.replace("/", "\\").split("\\")
        )
    ):
        raise ValueError("native part target must use an ordinary absolute path")
    if any(
        IsDeviceName(Value)
        or Value.endswith((".", " "))
        or any(Character in '<>:"|?*' for Character in Value)
        for Value in PathValue.parts[1:]
    ):
        raise ValueError("native part target contains an invalid windows name")
    return InputValue
