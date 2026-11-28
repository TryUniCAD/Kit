from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut

from convert.adapters.solidworks.Archive.Bodies.Fields.CacheCountField import (
    KCacheCountKind,
    KCacheSlotsMax,
)


# part cache groups use a signed count from the bounded ordinary archive profile
def ReadCacheNumMut(Cursor: BinaryReader) -> int:
    Probe = BinaryReader(Cursor.BytesValue, Cursor.OffsetValue)
    CountValue = CastValue(int, ReadScalarMut(Probe, KCacheCountKind))
    if not 0 <= CountValue <= KCacheSlotsMax:
        raise ValueError("native part cache count is outside zero through two")
    Cursor.OffsetValue = Probe.OffsetValue
    return CountValue
