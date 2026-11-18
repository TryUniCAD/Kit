from pathlib import PureWindowsPath

from convert.adapters.base.ContractTypes import IsDeviceName
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm


# invalid windows aliases must reject before either linked file can acquire a misleading or colliding identity
def CheckNativePath(PathValue: str) -> PureWindowsPath:
    ResultValue = PureWindowsPath(PathValue)
    RequireAsm(
        ResultValue.is_absolute() and bool(ResultValue.drive),
        "linked output requires an explicit absolute windows destination",
    )
    RequireAsm(
        not PathValue.startswith(("\\\\?\\", "\\\\.\\")),
        "linked output cannot use a device namespace",
    )
    PartsValue = PathValue.replace("/", "\\").split("\\")
    RequireAsm(
        not any(Value in (".", "..") for Value in PartsValue),
        "linked output cannot contain traversal components",
    )
    for PartValue in ResultValue.parts[1:]:
        RequireAsm(
            not IsDeviceName(PartValue) and not PartValue.endswith((".", " ")),
            "linked output contains a windows name alias",
        )
        RequireAsm(
            not any(ord(Value) < 32 or Value in '<>:"|?*' for Value in PartValue),
            "linked output contains an invalid windows component",
        )
    return ResultValue
