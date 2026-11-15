from __future__ import annotations as Annotations

from dataclasses import dataclass as DataClass

# legacy payloads carry class records as type six frames
KRecordType = 0x06
KNameFloor = 2
KNameCeiling = 64
KFrameTail = 4
KFirstText = 0x20
KLastText = 0x7F


# a legacy name is printable ascii without a fixed prefix
def ReadName(Payload: bytes, Cursor: int, Length: int) -> bytes | None:
    Symbols = Payload[Cursor : Cursor + Length]
    if len(Symbols) != Length:
        return None
    if not all(KFirstText <= SymbolValue < KLastText for SymbolValue in Symbols):
        return None
    return Symbols


# one class record of a legacy payload
@DataClass(frozen=True)
class LegacyClass:
    Schema: str
    SchemaFlag: int
    Name: str
    Value: int


# read one frame at an offset or return nothing when the bytes do not fit
def ReadFrame(Payload: bytes, Cursor: int) -> tuple[LegacyClass, int] | None:
    if Cursor < 0 or Cursor + 1 + 2 > len(Payload) or Payload[Cursor] != KRecordType:
        return None
    SchemaLength = int.from_bytes(Payload[Cursor + 1 : Cursor + 3], "little")
    if not KNameFloor <= SchemaLength <= KNameCeiling:
        return None
    SchemaAt = Cursor + 3
    SchemaEnd = SchemaAt + SchemaLength
    if SchemaEnd + KFrameTail > len(Payload):
        return None
    Schema = ReadName(Payload, SchemaAt, SchemaLength)
    if Schema is None:
        return None
    SchemaFlag = int.from_bytes(Payload[SchemaEnd : SchemaEnd + KFrameTail], "little")
    NameAt = SchemaEnd + KFrameTail
    if NameAt + 2 > len(Payload):
        return None
    NameLength = int.from_bytes(Payload[NameAt : NameAt + 2], "little")
    if not KNameFloor <= NameLength <= KNameCeiling:
        return None
    TextAt = NameAt + 2
    TextEnd = TextAt + NameLength
    if TextEnd + KFrameTail > len(Payload):
        return None
    ClassName = ReadName(Payload, TextAt, NameLength)
    if ClassName is None:
        return None
    Value = int.from_bytes(Payload[TextEnd : TextEnd + KFrameTail], "little")
    Record = LegacyClass(
        Schema.decode("ascii"), SchemaFlag, ClassName.decode("ascii"), Value
    )
    return (Record, TextEnd + KFrameTail)


# the table starts at the first offset that frames cleanly and then continues
def LegacyTable(Payload: bytes) -> tuple[LegacyClass, ...]:
    Start = -1
    for Cursor in range(0, len(Payload) - 3):
        if Payload[Cursor] != KRecordType:
            continue
        First = ReadFrame(Payload, Cursor)
        if First is None:
            continue
        Second = ReadFrame(Payload, First[1])
        if Second is not None:
            Start = Cursor
            break
    if Start < 0:
        raise ValueError("legacy NX payload does not carry a class table")
    Found: list[LegacyClass] = []
    Cursor = Start
    while Cursor < len(Payload):
        Frame = ReadFrame(Payload, Cursor)
        if Frame is None:
            break
        Found.append(Frame[0])
        Cursor = Frame[1]
    return tuple(Found)


# the table is a run of frames and its extent ends at the first non frame byte
def ClassTableEnd(Payload: bytes, Records: tuple[LegacyClass, ...]) -> int:
    Start = -1
    for Cursor in range(0, len(Payload) - 3):
        if Payload[Cursor] != KRecordType:
            continue
        First = ReadFrame(Payload, Cursor)
        if First is None:
            continue
        if ReadFrame(Payload, First[1]) is not None:
            Start = Cursor
            break
    if Start < 0 or not Records:
        raise ValueError("legacy NX payload does not carry a class table")
    Cursor = Start
    for _ in Records:
        Frame = ReadFrame(Payload, Cursor)
        if Frame is None:
            raise ValueError("legacy NX class table ends early")
        Cursor = Frame[1]
    return Cursor


__all__ = [
    "ClassTableEnd",
    "LegacyClass",
    "LegacyTable",
    "ReadFrame",
]
