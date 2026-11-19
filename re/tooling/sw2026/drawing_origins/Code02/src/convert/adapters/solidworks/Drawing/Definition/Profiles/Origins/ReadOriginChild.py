from hashlib import sha256 as HashBytes
from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Drawing.Definition.Profiles.Origins.OriginChild import (
    OriginChild,
)


def ReadOriginChild(
    DataValue: bytes, PathValue: object, ExpectedSha256: str
) -> OriginChild:
    if (
        not isinstance(PathValue, PureWindowsPath)
        or not PathValue.is_absolute()
        or PathValue.suffix.casefold() != ".sldprt"
        or type(ExpectedSha256) is not str
        or len(ExpectedSha256) != 64
        or any(Value not in "0123456789abcdef" for Value in ExpectedSha256)
        or HashBytes(DataValue).hexdigest() != ExpectedSha256
    ):
        raise ValueError(
            "drawing origin requires an explicit resolved path and exact child hash"
        )
    ArchiveValue = SldprtArchive.from_bytes(DataValue)
    LinkValue = ReadNativeLink(ArchiveValue, 0)
    if LinkValue.ConfigValue.RootValue.ClassValue.NameValue != "moPart_c":
        raise ValueError("drawing origin requires an actual ordinary part child")
    ManagerValue = ReadCmgrMut(ArchiveValue.require("Contents/CMgr"), 19000)
    return OriginChild(PathValue, ExpectedSha256, LinkValue, ManagerValue)
