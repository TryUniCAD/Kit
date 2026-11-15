from __future__ import annotations as Annotations

from dataclasses import dataclass as DataClass

# legacy payloads carry class records as type six frames
KRecordType = 0x06

# needed so kname floor stays a single named source for the nx adapter
KNameFloor = 2

# needed so kname ceiling stays a single named source for the nx adapter
KNameCeiling = 64

# needed so kframe tail stays a single named source for the nx adapter
KFrameTail = 4

# needed so kattribute type stays a single named source for the nx adapter
KAttributeType = 0x07

# needed so kscan window stays a single named source for the nx adapter
KScanWindow = 64

# needed so kfirst text stays a single named source for the nx adapter
KFirstText = 0x20

# needed so klast text stays a single named source for the nx adapter
KLastText = 0x7F


# a legacy name is printable ascii without a fixed prefix
def ReadName(Payload: bytes, Cursor: int, Length: int) -> bytes | None:
    Symbols = Payload[Cursor : Cursor + Length]
    if len(Symbols) != Length:
        return None
    if not all(KFirstText <= SymbolValue < KLastText for SymbolValue in Symbols):
        return None
    return Symbols


# one attribute record of a legacy payload
@DataClass(frozen=True)
class LegacyAttribute:
    Schema: str
    SchemaFlag: int
    ClassName: str
    Attribute: str
    Value: int


# a length prefixed name appears inside both record kinds
def ReadSpan(Payload: bytes, Cursor: int) -> tuple[str, int] | None:
    if Cursor + 2 > len(Payload):
        return None
    Length = int.from_bytes(Payload[Cursor : Cursor + 2], "little")
    if not KNameFloor <= Length <= KNameCeiling:
        return None
    NameText = ReadName(Payload, Cursor + 2, Length)
    if NameText is None:
        return None
    return (NameText.decode("ascii"), Cursor + 2 + Length)


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


# the frame run starts at the first offset where two frames parse in a row
def LegacyStart(Payload: bytes) -> int:
    for Cursor in range(0, len(Payload) - 3):
        if Payload[Cursor] != KRecordType:
            continue
        First = ReadFrame(Payload, Cursor)
        if First is None:
            continue
        if ReadFrame(Payload, First[1]) is not None:
            return Cursor
    raise ValueError("legacy NX payload does not carry a class table")


# the table starts at the first offset that frames cleanly and then continues
def LegacyTable(Payload: bytes) -> tuple[LegacyClass, ...]:
    Start = LegacyStart(Payload)
    Found: list[LegacyClass] = []
    Cursor = Start
    while Cursor < len(Payload):
        Frame = ReadFrame(Payload, Cursor)
        if Frame is None:
            break
        Found.append(Frame[0])
        Cursor = Frame[1]
    return tuple(Found)


# each class carries a code stored as a little endian word before the frames
def LegacyCodes(Payload: bytes) -> tuple[int, ...]:
    Start = LegacyStart(Payload)
    Records = LegacyTable(Payload)
    TableAt = Start - 2 * len(Records)
    if not Records or TableAt < 0:
        raise ValueError("legacy NX payload does not carry class codes")
    return tuple(
        int.from_bytes(Payload[TableAt + 2 * Index : TableAt + 2 * Index + 2], "little")
        for Index in range(len(Records))
    )


# the table is a run of frames and its extent ends at the first non frame byte
def ClassTableEnd(Payload: bytes, Records: tuple[LegacyClass, ...]) -> int:
    if not Records:
        raise ValueError("legacy NX payload does not carry a class table")
    Start = LegacyStart(Payload)
    Cursor = Start
    for _ in Records:
        Frame = ReadFrame(Payload, Cursor)
        if Frame is None:
            raise ValueError("legacy NX class table ends early")
        Cursor = Frame[1]
    return Cursor


# needed so all stays a single named source for the nx adapter
__all__ = [
    "ClassTableEnd",
    "LegacyAttribute",
    "LegacyAttrs",
    "LegacyClass",
    "LegacyCodes",
    "LegacyStart",
    "LegacyTable",
    "ReadFrame",
]


# an attribute record names a schema a class and one attribute followed by a value
def ReadAttribute(Payload: bytes, Cursor: int) -> tuple[LegacyAttribute, int] | None:
    if Cursor < 0 or Cursor + 3 > len(Payload) or Payload[Cursor] != KAttributeType:
        return None
    SchemaSpan = ReadSpan(Payload, Cursor + 1)
    if SchemaSpan is None or SchemaSpan[1] + 4 > len(Payload):
        return None
    SchemaFlag = int.from_bytes(Payload[SchemaSpan[1] : SchemaSpan[1] + 4], "little")
    ClassSpan = ReadSpan(Payload, SchemaSpan[1] + 4)
    if ClassSpan is None:
        return None
    AttrSpan = ReadSpan(Payload, ClassSpan[1])
    if AttrSpan is None or AttrSpan[1] + 4 > len(Payload):
        return None
    Value = int.from_bytes(Payload[AttrSpan[1] : AttrSpan[1] + 4], "little")
    Record = LegacyAttribute(
        SchemaSpan[0], SchemaFlag, ClassSpan[0], AttrSpan[0], Value
    )
    return (Record, AttrSpan[1] + 4)


# the attribute records follow the class frames and run consecutively
def LegacyAttrs(Payload: bytes) -> tuple[LegacyAttribute, ...]:
    Start = ClassTableEnd(Payload, LegacyTable(Payload))
    Cursor = -1
    for Probe in range(Start, min(Start + KScanWindow, len(Payload))):
        if ReadAttribute(Payload, Probe) is not None:
            Cursor = Probe
            break
    Found: list[LegacyAttribute] = []
    while Cursor >= 0:
        Frame = ReadAttribute(Payload, Cursor)
        if Frame is None:
            break
        Found.append(Frame[0])
        Cursor = Frame[1]
    return tuple(Found)
