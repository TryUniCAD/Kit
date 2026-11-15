from __future__ import annotations as Annotations

from dataclasses import dataclass as DataClass

# legacy payloads hold length prefixed object model sections
KMagic = b"OM\x01\x01"

# needed so kplatform at stays a single named source for the nx adapter
KPlatformAt = 0x17

# needed so kstamp width stays a single named source for the nx adapter
KStampWidth = 3

# needed so kcount length stays a single named source for the nx adapter
KCountLength = 8

# needed so kfloor version stays a single named source for the nx adapter
KFloorVersion = 1

# needed so kceiling version stays a single named source for the nx adapter
KCeilingVersion = 40

# needed so kfloor text stays a single named source for the nx adapter
KFloorText = 0x20

# needed so kceiling text stays a single named source for the nx adapter
KCeilingText = 0x7F

# needed so kfloor name stays a single named source for the nx adapter
KFloorName = 1

# needed so kceiling name stays a single named source for the nx adapter
KCeilingName = 255


# one object model section of a legacy payload
@DataClass(frozen=True)
class LegacySection:
    Offset: int
    Length: int
    Version: int
    KindValue: int
    StampValue: int
    Platform: str
    PartName: str
    Counts: tuple[int, ...]


# a section field is text when it is printable ascii of a sane length
def ReadText(Payload: bytes, Cursor: int, Length: int) -> str | None:
    Symbols = Payload[Cursor : Cursor + Length]
    if len(Symbols) != Length:
        return None
    if not all(KFloorText <= SymbolValue < KCeilingText for SymbolValue in Symbols):
        return None
    return Symbols.decode("ascii")


# the section header ends with eight little endian counts
def ReadCounts(Payload: bytes, Cursor: int) -> tuple[int, ...] | None:
    if Cursor + 4 * KCountLength > len(Payload):
        return None
    return tuple(
        int.from_bytes(Payload[Cursor + 4 * Index : Cursor + 4 * Index + 4], "little")
        for Index in range(KCountLength)
    )


# the platform and part name are length prefixed ascii runs
def ReadHeaderText(Payload: bytes, Cursor: int) -> tuple[str, str, int] | None:
    PlatformLength = int.from_bytes(Payload[Cursor + 0x13 : Cursor + 0x17], "little")
    if not KFloorName <= PlatformLength <= KCeilingName:
        return None
    Platform = ReadText(Payload, Cursor + KPlatformAt, PlatformLength)
    if Platform is None:
        return None
    NameAt = Cursor + KPlatformAt + PlatformLength
    if NameAt + 4 > len(Payload):
        return None
    NameLength = int.from_bytes(Payload[NameAt : NameAt + 4], "little")
    if not KFloorName <= NameLength <= KCeilingName:
        return None
    PartName = ReadText(Payload, NameAt + 4, NameLength)
    if PartName is None:
        return None
    return (Platform, PartName, NameAt + 4 + NameLength)


# one section header is magic version kind stamp platform name and counts
def ReadSection(Payload: bytes, Cursor: int) -> LegacySection | None:
    if Cursor < 4 or Cursor + KPlatformAt > len(Payload):
        return None
    if Payload[Cursor : Cursor + 4] != KMagic:
        return None
    Length = int.from_bytes(Payload[Cursor - 4 : Cursor], "big")
    if Length < KPlatformAt or Cursor + Length > len(Payload):
        return None
    Version = int.from_bytes(Payload[Cursor + 4 : Cursor + 8], "big")
    if not KFloorVersion <= Version <= KCeilingVersion:
        return None
    KindValue = int.from_bytes(Payload[Cursor + 8 : Cursor + 12], "big")
    StampValue = int.from_bytes(Payload[Cursor + 0x10 : Cursor + 0x13], "big")
    Header = ReadHeaderText(Payload, Cursor)
    if Header is None:
        return None
    Counts = ReadCounts(Payload, Header[2])
    if Counts is None:
        return None
    return LegacySection(
        Cursor, Length, Version, KindValue, StampValue, Header[0], Header[1], Counts
    )


# sections appear in order and each one ends before the next begins
def ReadSections(Payload: bytes) -> tuple[LegacySection, ...]:
    Output: list[LegacySection] = []
    Cursor = 4
    while True:
        Found = Payload.find(KMagic, Cursor)
        if Found < 0:
            break
        Section = ReadSection(Payload, Found)
        if Section is None:
            Cursor = Found + 4
            continue
        Output.append(Section)
        Cursor = max(Found + 4, Found - 4 + Section.Length + 4)
    return tuple(Output)


# needed so all stays a single named source for the nx adapter
__all__ = [
    "LegacySection",
    "ReadSection",
    "ReadSections",
]
