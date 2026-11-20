from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# a child section needs an absolute end without moving the parent cursor
def ReadSectSpan(Cursor: BinaryReader) -> BinaryReader:
    Section = BinaryReader(Cursor.BytesValue, Cursor.OffsetValue, Cursor.LimitValue)
    ByteCount = Section.ReadUnsigned(4)
    if ByteCount > Section.GetRemaining():
        raise ValueError("SOLIDWORKS model section exceeds its remaining stream")
    Section.LimitValue = Section.GetOffset() + ByteCount
    return Section
