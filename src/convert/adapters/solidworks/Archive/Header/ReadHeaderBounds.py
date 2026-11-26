from math import isfinite as IsFinite
from struct import Struct

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader

# the native bbox stores a centre extrema and an independent sphere radius
KHeaderBox = Struct("<10d")


# present bounds must remain finite before consumers use them as geometry
def ReadBoundsMut(Cursor: BinaryReader) -> tuple[float, ...] | None:
    Presence = Cursor.ReadUnsigned(4)
    if Presence == 0:
        return None
    if Presence != 1:
        raise ValueError("invalid SOLIDWORKS header bounding box presence flag")
    Values = tuple(
        float(Value) for Value in KHeaderBox.unpack(Cursor.TakeBytes(KHeaderBox.size))
    )
    if not all(IsFinite(Value) for Value in Values) or Values[9] < 0:
        raise ValueError("invalid SOLIDWORKS header bounding box")
    return Values
