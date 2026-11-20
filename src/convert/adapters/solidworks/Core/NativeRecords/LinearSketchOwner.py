from math import isfinite as IsFinite
from struct import Struct as FieldLayout

# current sketch array rows carry a record flag and two entity identities
KEntityIdentity = FieldLayout("<Hii")

# optional branches must be absent for a fixed width ordinary entity prefix
KOrdinaryEntity = FieldLayout("<21xH12xHHH4xHB16x")

# two dimensional points retain their state flags before the coordinates
KPointPosition = FieldLayout("<Hdd")

# ordinary line rows store compact endpoint slots and segment state
KLineTail = FieldLayout("<HHHHdH")

# these counted arrays follow the last line in current sketch serialization
KFollowingArrays = FieldLayout("<iii")

# an ordinary rectangle has four typed point slots and four line slots
KVertexCount = 4

# the count precedes the first embedded entity identity in each array
KArrayCount = FieldLayout("<i")

# current ordinary line rows include the entity identity outside the marker prefix
KLineWidth = KEntityIdentity.size + KOrdinaryEntity.size + KLineTail.size


# circle inference can be skipped only for an owned sketch with an empty arc array
def HasLineOnlyRect(
    DataValue: bytes, Markers: tuple[int, ...], Start: int, EndValue: int
) -> bool:
    if Start < 0 or EndValue > len(DataValue) or len(Markers) != 2 * KVertexCount:
        return False
    Points = Markers[:KVertexCount]
    Lines = Markers[KVertexCount:]
    FirstPointCount = Points[0] - KEntityIdentity.size - KArrayCount.size
    FirstLineCount = Lines[0] - KEntityIdentity.size - KArrayCount.size
    Arrays = Lines[-1] + KOrdinaryEntity.size + KLineTail.size
    if (
        not Start
        <= FirstPointCount
        < FirstLineCount
        < Arrays
        <= EndValue - KFollowingArrays.size
    ):
        return False
    if KArrayCount.unpack_from(DataValue, FirstPointCount)[0] != KVertexCount:
        return False
    if KArrayCount.unpack_from(DataValue, FirstLineCount)[0] != KVertexCount:
        return False
    if not HasPointRows(DataValue, Points, FirstLineCount):
        return False
    if not HasLineRing(DataValue, Lines):
        return False
    return KFollowingArrays.unpack_from(DataValue, Arrays) == (0, 0, 0)


# the embedded point headers identify local slots independently of style markers
def HasPointRows(DataValue: bytes, Points: tuple[int, ...], EndValue: int) -> bool:
    for SlotId, (Offset, Limit) in enumerate(
        zip(Points, (*Points[1:], EndValue), strict=True), 1
    ):
        FlagOffset = Offset + KOrdinaryEntity.size
        if FlagOffset + KPointPosition.size > Limit:
            return False
        if KEntityIdentity.unpack_from(DataValue, Offset - KEntityIdentity.size) != (
            0,
            0,
            SlotId,
        ):
            return False
        if KOrdinaryEntity.unpack_from(DataValue, Offset) != (0, 0, 4, 0, 0, 0):
            return False
        State, XValue, YValue = KPointPosition.unpack_from(DataValue, FlagOffset)
        if State != 0x1E or not IsFinite(XValue) or not IsFinite(YValue):
            return False
    return True


# fixed width line rows prove that adjacent point slots are straight edge endpoints
def HasLineRing(DataValue: bytes, Lines: tuple[int, ...]) -> bool:
    if Lines != tuple(Lines[0] + SlotId * KLineWidth for SlotId in range(KVertexCount)):
        return False
    Owners: set[int] = set()
    Cycle: set[frozenset[int]] = set()
    for SlotId, Offset in enumerate(Lines, 1):
        Flags, Owner, Local = KEntityIdentity.unpack_from(
            DataValue, Offset - KEntityIdentity.size
        )
        if Flags or Owner <= 0 or Local != SlotId or Owner in Owners:
            return False
        if KOrdinaryEntity.unpack_from(DataValue, Offset) != (0, 0, 4, 0, 0, 0):
            return False
        First, Second, *_ = KLineTail.unpack_from(
            DataValue, Offset + KOrdinaryEntity.size
        )
        if First >= KVertexCount or Second >= KVertexCount or First == Second:
            return False
        Owners.add(Owner)
        Cycle.add(frozenset((First, Second)))
    return Cycle == {
        frozenset((SlotId, (SlotId + 1) % KVertexCount))
        for SlotId in range(KVertexCount)
    }
