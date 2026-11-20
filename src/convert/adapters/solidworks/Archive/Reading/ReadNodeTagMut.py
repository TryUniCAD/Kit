from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag


# references must resolve at the depth limit without opening another body
def ReadNodeTagMut(
    Cursor: BinaryReader, NestingDepth: int, MaxDepth: int
) -> ArchiveTag:
    TagValue, Offset = ReadTag(Cursor.BytesValue, Cursor.OffsetValue)
    if TagValue.KindValue in ("NewClass", "ClassRef") and NestingDepth >= MaxDepth:
        raise ValueError("SOLIDWORKS archive nesting exceeds the supported depth")
    Cursor.OffsetValue = Offset
    return TagValue
