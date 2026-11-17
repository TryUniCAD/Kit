from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.ReadString import ReadString


# archive fields retain their text encoding when they are written again
def ReadCStringMut(Cursor: BinaryReader) -> CStringValue:
    StringValue, Offset = ReadString(Cursor.BytesValue, Cursor.OffsetValue)
    Cursor.OffsetValue = Offset
    return StringValue


# text projections use the same cursor operation as lossless header readers
def ReadTextMut(Cursor: BinaryReader) -> str:
    return ReadCStringMut(Cursor).TextValue
