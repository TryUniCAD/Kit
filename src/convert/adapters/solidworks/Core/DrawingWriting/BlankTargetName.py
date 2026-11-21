from pathlib import Path as FilePath, PureWindowsPath

from convert.adapters.base.ContractTypes import IsDeviceName, KTargetType
from convert.adapters.solidworks.Container.Format import KDrawingSuffix
from interchange.document.Models.DocumentModel import CadDocument


# the drawing name must be valid in the native locator and preserve an explicitly authored name
def BlankTargetName(DocumentValue: CadDocument, TargetValue: KTargetType) -> str:
    if not isinstance(TargetValue, (str, FilePath)):
        raise TypeError("native blank drawing output requires a filesystem path")
    PathValue = FilePath(TargetValue)
    NameValue = PathValue.stem
    if (
        PathValue.suffix.casefold() != KDrawingSuffix
        or not NameValue
        or PureWindowsPath(PathValue.name).name != PathValue.name
        or IsDeviceName(PathValue.name)
        or NameValue.endswith((".", " "))
        or any(ord(Character) < 32 or Character in '<>:"|?*' for Character in NameValue)
        or DocumentValue.metadata.get("name", NameValue) != NameValue
    ):
        raise ValueError("native blank drawing requires a valid matching SLDDRW name")
    return NameValue
