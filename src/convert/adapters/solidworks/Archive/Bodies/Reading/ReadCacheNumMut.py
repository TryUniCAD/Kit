from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# part cache groups use a signed count from the bounded ordinary archive profile
def ReadCacheNumMut(Cursor: BinaryReader) -> int:
    Probe = BinaryReader(Cursor.BytesValue, Cursor.OffsetValue)
    CountValue = CastValue(int, ReadScalarMut(Probe, "i32"))
    if not 0 <= CountValue <= 2:
        raise ValueError("native part cache count is outside zero through two")
    Cursor.OffsetValue = Probe.OffsetValue
    return CountValue
