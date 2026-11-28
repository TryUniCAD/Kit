from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag


# stream prefix readers advance past a wire tag without opening a graph body
def ReadTagMut(Cursor: BinaryReader) -> ArchiveTag:
    TagValue, Offset = ReadTag(Cursor.BytesValue, Cursor.OffsetValue)
    Cursor.OffsetValue = Offset
    return TagValue
