from uuid import UUID as UuidValue

from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo

# fixed resource stamps make the nested archive fixture reproducible
KResourceStamp = "2026-01-01T00:00:00Z"


# separate core identities keep nested fixture ownership independent of native resources
def MakeResCore(Index: int, NameValue: str) -> PackageCore:
    return PackageCore(
        str(UuidValue(int=Index)), KResourceStamp, KResourceStamp, 1, NameValue
    )


# independent binary contents exercise ordering within a leaf as well as between branches
def MakeResBranch(Index: int, Label: str) -> PackageFolder:
    LeafValue = PackageFolder(
        MakeResCore(Index + 1, "leaf"),
        Links=tuple(
            ResourceInfo(
                NameValue,
                NameValue + ".bin",
                "application/octet-stream",
                KResourceStamp,
            )
            for NameValue in ("second", "first")
        ),
        Contents=(b"\x00\xff" + Label.encode(), b"\x80\x09" + Label.encode()),
    )
    return PackageFolder(MakeResCore(Index, Label), (LeafValue,))


# deliberately nonalphabetic branches detect an accidental sort during json transport
def MakeResTree() -> PackageFolder:
    return PackageFolder(
        MakeResCore(1, "Resources"),
        (MakeResBranch(10, "zeta"), MakeResBranch(20, "alpha")),
    )
