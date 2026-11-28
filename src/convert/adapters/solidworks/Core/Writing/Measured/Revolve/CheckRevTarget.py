from os import name as OsName
from pathlib import Path as FilePath, PureWindowsPath
from sys import platform as PlatformName

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.Staging.PathStageOwner import KPathStageOwner


# an encoded mac home locator belongs to the actual measured shared path or one standalone stream
def CheckRevTarget(
    TargetValue: KTargetType, OptionsValue: WriteOptions, Locator: str
) -> None:
    Requested = OptionsValue.values.get("final_destination")
    if not isinstance(TargetValue, FilePath):
        if Requested != Locator:
            raise ValueError(
                "measured revolve stream requires its exact inspected self locator"
            )
        return
    Owner = KPathStageOwner.get()
    Actual = Owner[1] if Owner is not None and Owner[0] == TargetValue else TargetValue
    Native = PureWindowsPath(Locator)
    Expected = (
        FilePath(Native)
        if OsName == "nt"
        else FilePath.home().joinpath(*Native.parts[1:])
    )
    if (
        (OsName != "nt" and PlatformName != "darwin")
        or TargetValue.name != Native.name
        or Actual != Expected
        or Requested not in (None, Locator, str(Actual))
    ):
        raise ValueError(
            "measured revolve filesystem destination differs from its inspected locator"
        )
