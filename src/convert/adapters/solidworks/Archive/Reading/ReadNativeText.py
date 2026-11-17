from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Strings.ReadString import ReadString


# native streams must share the archive string encoding and consume its exact width
def ReadTextMut(Cursor: BinaryReader) -> str:
    StringValue, Offset = ReadString(Cursor.BytesValue, Cursor.OffsetValue)
    Cursor.OffsetValue = Offset
    return StringValue.TextValue
