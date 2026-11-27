from convert.adapters.solidworks.Archive.Header.HeaderBoundsField import (
    HasFiniteBounds,
    KBoundsAbsent,
    KBoundsPresence,
    KBoundsPresent,
    KBoundsRadiusIndex,
    KHeaderBox,
)

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# present bounds must remain finite before consumers use them as geometry
def ReadBoundsMut(Cursor: BinaryReader) -> tuple[float, ...] | None:
    Presence = KBoundsPresence.unpack(Cursor.TakeBytes(KBoundsPresence.size))[0]
    if Presence == KBoundsAbsent:
        return None
    if Presence != KBoundsPresent:
        raise ValueError("invalid SOLIDWORKS header bounding box presence flag")
    Values = tuple(
        float(Value) for Value in KHeaderBox.unpack(Cursor.TakeBytes(KHeaderBox.size))
    )
    if not HasFiniteBounds(Values) or Values[KBoundsRadiusIndex] < 0:
        raise ValueError("invalid SOLIDWORKS header bounding box")
    return Values
