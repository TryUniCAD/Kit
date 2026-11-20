from hashlib import sha256
from CmgrColorReadback import ReadColorSpan
from CmgrOpening import ReadCmgrOpening
from CmgrVisualPrefix import (
    CmgrVisualFields,
    WriteCmgrVisualPrefix,
)
from ReadCmgrVisualPrefix import ReadCmgrVisualPrefix
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# Fixed scalar and CString groups are validated by the exact reconstruction.
def read_visual_fields(cursor: FieldCursor) -> CmgrVisualFields:
    return ReadCmgrVisualPrefix(cursor, 19000, AllowSystemTexture=True)


def verify_visual_prefix(stream: bytes, generation: int, asset: str) -> str:
    cursor = ReadCmgrOpening(stream, generation)
    start = cursor.Offset
    fields = read_visual_fields(cursor)
    _, dspbr_start, _ = ReadColorSpan(stream, generation)
    RequireArch(
        cursor.Offset,
        dspbr_start,
        f"CMgr material and RealView boundaries in {asset}",
    )
    writer = ArchiveWriter()
    writer.SetNextIndex(cursor.NextIndex)
    writer.classes.update((name, index) for index, name in cursor.Classes.items())
    WriteCmgrVisualPrefix(writer, generation, fields)
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, {name: index for index, name in cursor.Classes.items()}),
        "CMgr visual prefix allocations",
    )
    saved = stream[start:dspbr_start]
    RequireArch(
        writer.build() == saved,
        True,
        f"CMgr material and RealView reconstruction in {asset}",
    )
    return sha256(saved).hexdigest()
