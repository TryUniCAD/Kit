from pathlib import PureWindowsPath
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)


# the detached resource uses the system data token while the live owner retains the requested installation alias
def LookResource(InputValue: PartLookInput, *, Holder: bool) -> str:
    if (
        type(CastValue(object, InputValue.DataDirectory)) is not str
        or type(CastValue(object, InputValue.ResourceName)) is not str
        or InputValue.ResourceName != r"graphics\materials\color.p2m"
        or not InputValue.DataDirectory.isascii()
        or not InputValue.DataDirectory.isprintable()
    ):
        raise ValueError(
            "part rendering requires an explicit ordinary stock color resource"
        )
    MountValue = PureWindowsPath(InputValue.DataDirectory)
    if (
        not MountValue.is_absolute()
        or len(MountValue.drive) != 2
        or MountValue.name.casefold() != "data"
        or str(MountValue) != InputValue.DataDirectory
        or any(Value in (".", "..") for Value in MountValue.parts)
    ):
        raise ValueError(
            "part rendering requires an absolute Windows data-directory alias"
        )
    return (
        (r"<SystemTexture>" if Holder else InputValue.DataDirectory)
        + "\\"
        + InputValue.ResourceName
    )
