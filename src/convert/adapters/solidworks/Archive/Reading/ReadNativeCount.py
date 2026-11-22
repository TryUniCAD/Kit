from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# count domains are shared while record owners supply their minimum wire size
def ReadCountMut(Cursor: BinaryReader, MinItemSize: int) -> int:
    Count, Offset = ReadCount(
        Cursor.BytesValue, Cursor.OffsetValue, LimitValue=Cursor.LimitValue
    )
    if Count > (Cursor.GetEnd() - Offset) // MinItemSize:
        raise ValueError("archive count exceeds the remaining stream size")
    Cursor.OffsetValue = Offset
    return Count
