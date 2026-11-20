from pathlib import PurePosixPath

from CmgrOpening import ReadCmgrOpening
from ReadCmgrVisualPrefix import ReadCmgrVisualPrefix, ReadMaterialFields
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)


# the post-material color record is preceded by the inline RealView appearance
def ReadRealView(Cursor: FieldCursor) -> None:
    Material = ReadMaterialFields(Cursor)
    MaterialPath = PurePosixPath(Material["NativeAssetPath"].replace("\\", "/"))
    RequireArch(MaterialPath.name.casefold(), "color.p2m", "CMgr RealView color file")


# the same typed archive object can carry the inline visual body in either stream
def ReadVisualSpan(Cursor: ArchiveCursor) -> tuple[int, int, ArchiveCursor]:
    Fields = ReadCmgrVisualPrefix(Cursor, 19000, AllowSystemTexture=True)
    Start = Cursor.Offset
    ReadColorDspbr(Cursor)
    return Fields.SurfaceColor, Start, Cursor


# independent prefix and dspbr ownership allows callers to consume each typed body exactly once
def ReadColorDspbr(Cursor: FieldCursor) -> None:
    _ = Cursor.ReadValue("<26fi18fi2f")
    Paths = tuple(Cursor.ReadText() for _ in range(4))
    RequireArch((Paths, Cursor.ReadText()), (("",) * 4, "basic"), "CMgr DSPBR subtype")
    _ = Cursor.ReadValue("<f")
    RequireArch(
        (Cursor.ReadText(), Cursor.ReadText()),
        ("2025x", ""),
        "CMgr DSPBR library version",
    )
    _ = Cursor.ReadValue("<i6f")
    Paths = tuple(Cursor.ReadText() for _ in range(2))
    _ = Cursor.ReadValue("<2f")
    Paths += tuple(Cursor.ReadText() for _ in range(3))
    RequireArch(Paths, ("",) * 5, "CMgr DSPBR texture paths")


def ReadColorSpan(BlobValue: bytes, Generation: int) -> tuple[int, int, ArchiveCursor]:
    return ReadVisualSpan(ReadCmgrOpening(BlobValue, Generation))
