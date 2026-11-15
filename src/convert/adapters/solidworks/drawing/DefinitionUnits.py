from __future__ import annotations

from dataclasses import dataclass
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError

# the entry width is needed because the tail has no length prefix
KUnitEntrySize = 16


# callers need the unit type conversion value and unit index as one value
@dataclass(frozen=True, slots=True)
class UnitEntry:
    Type: int
    Value: float
    Unit: int


# callers need the entries and the preserved tail as one value
@dataclass(frozen=True, slots=True)
class UnitTable:
    Entries: tuple[UnitEntry, ...]
    Tail: bytes


# the count and entry width bound the read so a truncated table is rejected
def UnitTableAt(DataValue: bytes) -> UnitTable:
    if len(DataValue) < 4:
        raise SldprtFormatError("drawing units table is truncated")
    (Count,) = Struct.unpack_from("<I", DataValue, 0)
    Offset = 4
    if Offset + Count * KUnitEntrySize > len(DataValue):
        raise SldprtFormatError("drawing units table is truncated")
    Entries: list[UnitEntry] = []
    for _ in range(Count):
        TypeValue, Value, UnitValue = Struct.unpack_from("<IdI", DataValue, Offset)
        Entries.append(UnitEntry(TypeValue, Value, UnitValue))
        Offset += KUnitEntrySize
    return UnitTable(tuple(Entries), DataValue[Offset:])


# the writer needs the exact entry order and tail to keep the table valid
def EncodeUnitTable(Table: UnitTable) -> bytes:
    Output = bytearray()
    Output.extend(Struct.pack("<I", len(Table.Entries)))
    for Entry in Table.Entries:
        Output.extend(Struct.pack("<IdI", Entry.Type, Entry.Value, Entry.Unit))
    Output.extend(Table.Tail)
    return bytes(Output)
