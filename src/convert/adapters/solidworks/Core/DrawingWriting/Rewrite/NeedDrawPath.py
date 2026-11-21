from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import IsDeviceName, KTargetType
from convert.adapters.solidworks.Container.Format import KDrawingSuffix


# a rewritten physical basename must remain valid without renaming the independently authored model title
def NeedDrawPath(TargetValue: KTargetType) -> None:
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError("native blank rewrite requires a filesystem path")
    PathValue = FilePath(TargetValue)
    NameValue = PathValue.stem
    if (
        PathValue.suffix.casefold() != KDrawingSuffix
        or not NameValue
        or PureWindowsPath(PathValue.name).name != PathValue.name
        or IsDeviceName(PathValue.name)
        or NameValue.endswith((".", " "))
        or any(ord(Character) < 32 or Character in '<>:"|?*' for Character in NameValue)
    ):
        raise ValueError("native blank rewrite requires an ordinary SLDDRW destination")
