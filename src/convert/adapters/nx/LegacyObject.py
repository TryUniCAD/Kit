from __future__ import annotations as Annotations

from dataclasses import dataclass as DataClass

from .LegacySection import LegacySection

# a legacy object area is addressed by a monotone section relative index
KIndexFloor = 1
KIndexCeiling = 4000
KIndexTailFloor = 4096


# the entity index and object table that frame every legacy object area
@DataClass(frozen=True)
class LegacyIndex:
    Offset: int
    Entries: tuple[int, ...]
    Count: int
    ObjectEnd: int


# one object record bounded by two section relative index entries
@DataClass(frozen=True)
class LegacyRecord:
    Offset: int
    Length: int
    ObjectId: int | None


# a strictly increasing run of little endian words seeded with zero
def ReadRun(Payload: bytes, Cursor: int, End: int) -> tuple[int, ...]:
    Values: list[int] = []
    while Cursor + 4 <= End:
        Value = int.from_bytes(Payload[Cursor : Cursor + 4], "little")
        if Values and Value <= Values[-1]:
            break
        Values.append(Value)
        Cursor += 4
    return tuple(Values)


# the index is the unique run whose second word equals the object table end
def ReadIndex(Payload: bytes, Section: LegacySection) -> LegacyIndex | None:
    End = min(Section.Offset + Section.Length, len(Payload))
    Floor = max(Section.Length - KIndexTailFloor, 0)
    Found: list[LegacyIndex] = []
    for Cursor in range(Section.Offset, max(End - 8, Section.Offset)):
        if Payload[Cursor] != 0 or Payload[Cursor + 1] != 0:
            continue
        if Payload[Cursor + 2] != 0 or Payload[Cursor + 3] != 0:
            continue
        Entries = ReadRun(Payload, Cursor, End)
        if len(Entries) < 3:
            continue
        CountAt = Cursor + 4 * len(Entries)
        if CountAt + 4 > End:
            continue
        Count = int.from_bytes(Payload[CountAt : CountAt + 4], "little")
        if not KIndexFloor <= Count <= KIndexCeiling:
            continue
        ObjectEnd = CountAt + 4 + 4 * Count
        if ObjectEnd > End:
            continue
        if Entries[1] != ObjectEnd - Section.Offset:
            continue
        if not Floor <= Entries[-1] <= Section.Length:
            continue
        Found.append(LegacyIndex(Cursor, Entries, Count, ObjectEnd))
    if not Found:
        return None
    return Found[0]


# object identifiers live in a count prefixed table that ends the index frame
def ReadObjects(Payload: bytes, Index: LegacyIndex) -> tuple[int | None, ...]:
    Start = Index.Offset + 4 * len(Index.Entries) + 4
    return tuple(
        int.from_bytes(Payload[Start + 4 * Slot : Start + 4 * Slot + 4], "little")
        for Slot in range(Index.Count)
    )


# record zero opens at the object table end and every later record at an index entry
def ReadRecords(
    Payload: bytes, Section: LegacySection, Index: LegacyIndex
) -> tuple[LegacyRecord, ...]:
    Objects = ReadObjects(Payload, Index)
    Output: list[LegacyRecord] = []
    for Position in range(len(Index.Entries) - 2):
        Start = (
            Index.ObjectEnd
            if Position == 0
            else Section.Offset + Index.Entries[Position + 1]
        )
        Stop = Section.Offset + Index.Entries[Position + 2]
        if not Index.ObjectEnd <= Start <= Stop <= Section.Offset + Section.Length:
            return ()
        Output.append(
            LegacyRecord(
                Start,
                Stop - Start,
                Objects[Position] if Position < len(Objects) else None,
            )
        )
    return tuple(Output)


__all__ = [
    "LegacyIndex",
    "LegacyRecord",
    "ReadIndex",
    "ReadObjects",
    "ReadRecords",
]
