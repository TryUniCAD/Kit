from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.creo.CreoFormat import CreoFormat

KMaxSections = 100000
KMaxSectionBytes = 64 * 1024 * 1024
KMaxCodes = 1 << 17


@dataclass(frozen=True, slots=True)
class CreoEntry:
    name: str
    offset: int
    length: int
    expanded: int
    kind: str
    checksum_a: int
    checksum_b: int


@dataclass(frozen=True, slots=True)
class CreoToc:
    entries: tuple[CreoEntry, ...]
    notes: tuple[str, ...]


def ParseHex(ValueText: str) -> int | None:
    try:
        return int(ValueText, 16)
    except ValueError:
        return None


def FindMarker(DataValue: bytes, Marker: bytes, Start: int) -> int:
    if Start < 0 or Start >= len(DataValue):
        return -1
    return DataValue.find(Marker, Start)


def ReadRows(
    DataValue: bytes, Start: int, Count: int, Width: int
) -> tuple[list[list[str]], int]:
    Rows: list[list[str]] = []
    Position = Start
    for _ in range(Count):
        EndValue = Position + Width
        if EndValue > len(DataValue):
            raise CreoFormat("Creo table of contents is truncated")
        RowText = DataValue[Position:EndValue].decode("latin-1")
        Words = RowText.rstrip("#\r\n").split()
        Rows.append(Words)
        Position = EndValue
    return Rows, Position


def ReadToc(DataValue: bytes, BaseValue: int) -> CreoToc:
    Entries: list[CreoEntry] = []
    Notes: list[str] = []
    Seen: set[int] = set()
    Position = FindMarker(DataValue, b"#UGC_TOC", BaseValue)
    if Position < 0:
        raise CreoFormat("Creo file has no table of contents")
    while Position not in Seen and len(Entries) < KMaxSections:
        Seen.add(Position)
        LineEnd = DataValue.find(b"\n", Position)
        if LineEnd < 0:
            raise CreoFormat("Creo table header is truncated")
        HeadText = DataValue[Position:LineEnd].decode("latin-1")
        Words = HeadText.rstrip("#\r").split()
        if len(Words) < 4 or Words[0] != "#UGC_TOC":
            raise CreoFormat("Creo table header is invalid")
        CountValue = int(Words[2], 10)
        WidthValue = int(Words[3], 10)
        if CountValue < 0 or CountValue > KMaxSections:
            raise CreoFormat("Creo table entry count is invalid")
        if WidthValue < 32 or WidthValue > 4096:
            raise CreoFormat("Creo table row width is invalid")
        Rows, _ = ReadRows(DataValue, LineEnd + 1, CountValue, WidthValue)
        NextTable: int | None = None
        for RowValue in Rows:
            if not RowValue:
                continue
            NameText = RowValue[0]
            if len(RowValue) < 4:
                Notes.append(f"Creo table row {NameText!r} is incomplete")
                continue
            OffsetValue = ParseHex(RowValue[1])
            LengthValue = ParseHex(RowValue[2])
            ExpandedValue = ParseHex(RowValue[3])
            if OffsetValue is None or LengthValue is None or ExpandedValue is None:
                Notes.append(f"Creo table row {NameText!r} has invalid numbers")
                continue
            Absolute = BaseValue + OffsetValue
            if NameText == "NEXT_TOC_ENTRY":
                NextTable = Absolute
                continue
            SectionEnd = Absolute + LengthValue
            Expected = b"#" + NameText.encode("latin-1") + b"\n"
            if (
                Absolute < 0
                or LengthValue < len(Expected)
                or SectionEnd > len(DataValue)
                or not DataValue.startswith(Expected, Absolute)
            ):
                Notes.append(f"Creo table row {NameText!r} has an invalid extent")
                continue
            KindText = RowValue[5] if len(RowValue) > 5 else ""
            ChecksumA = ParseHex(RowValue[7]) if len(RowValue) > 7 else 0
            ChecksumB = ParseHex(RowValue[8]) if len(RowValue) > 8 else 0
            Entries.append(
                CreoEntry(
                    name=NameText,
                    offset=Absolute,
                    length=LengthValue,
                    expanded=ExpandedValue,
                    kind=KindText,
                    checksum_a=ChecksumA or 0,
                    checksum_b=ChecksumB or 0,
                )
            )
        if NextTable is None:
            break
        Found = FindMarker(DataValue, b"#UGC_TOC", max(0, NextTable - 8))
        if Found < 0 or Found > NextTable + 64:
            Notes.append("Creo continuation table is missing")
            break
        Position = Found
    return CreoToc(tuple(Entries), tuple(Notes))


def SkipGroup(
    Position: int,
    BitBuffer: int,
    BitCount: int,
    GroupCount: int,
    CodeSize: int,
    DataValue: bytes,
) -> tuple[int, int, int]:
    Remainder = (8 - GroupCount % 8) % 8
    SkipBits = Remainder * CodeSize
    while SkipBits > 0:
        if BitCount == 0:
            if Position >= len(DataValue):
                return (Position, BitBuffer, BitCount)
            BitBuffer = DataValue[Position]
            Position += 1
            BitCount = 8
        Taken = min(SkipBits, BitCount)
        BitBuffer >>= Taken
        BitCount -= Taken
        SkipBits -= Taken
    return (Position, BitBuffer, BitCount)


def Uncompress(DataValue: bytes, Expected: int) -> bytes:
    if len(DataValue) < 4 or DataValue[:2] != b"\x1f\x9d":
        raise CreoFormat("Creo section is not Unix-compressed")
    Flags = DataValue[2]
    MaxBits = Flags & 0x1F
    if MaxBits < 9 or MaxBits > 16:
        raise CreoFormat("Creo compression code width is invalid")
    BlockMode = bool(Flags & 0x80)
    Limit = min(max(Expected, 1), KMaxSectionBytes)
    Prefixes = list(range(256))
    LastBytes = list(range(256))
    if BlockMode:
        Prefixes.append(0)
        LastBytes.append(0)
    Position = 3
    BitBuffer = 0
    BitCount = 0
    CodeSize = 9
    GroupCount = 0
    Previous: int | None = None
    Output = bytearray()
    while len(Output) < Limit:
        while BitCount < CodeSize:
            if Position >= len(DataValue):
                return bytes(Output)
            BitBuffer |= DataValue[Position] << BitCount
            Position += 1
            BitCount += 8
        CodeValue = BitBuffer & ((1 << CodeSize) - 1)
        BitBuffer >>= CodeSize
        BitCount -= CodeSize
        GroupCount += 1
        if BlockMode and CodeValue == 256:
            del Prefixes[257:]
            del LastBytes[257:]
            Position, BitBuffer, BitCount = SkipGroup(
                Position, BitBuffer, BitCount, GroupCount, CodeSize, DataValue
            )
            CodeSize = 9
            GroupCount = 0
            Previous = None
            continue
        TableSize = len(Prefixes)
        if Previous is None:
            if CodeValue >= TableSize:
                raise CreoFormat("Creo compression first code is invalid")
            EntryCode = CodeValue
            AddFirst = False
        elif CodeValue < TableSize:
            EntryCode = CodeValue
            AddFirst = False
        elif CodeValue == TableSize and Previous is not None:
            EntryCode = Previous
            AddFirst = True
        else:
            raise CreoFormat("Creo compression code is outside the table")
        Stack = bytearray()
        Cursor = EntryCode
        Guard = 0
        while True:
            if Cursor >= len(Prefixes) or Cursor >= len(LastBytes):
                raise CreoFormat("Creo compression prefix is invalid")
            Stack.append(LastBytes[Cursor])
            if Cursor < 256:
                break
            Cursor = Prefixes[Cursor]
            Guard += 1
            if Guard > KMaxCodes:
                raise CreoFormat("Creo compression dictionary loops")
        FirstByte = Stack[-1] if Stack else 0
        if len(Output) + len(Stack) + int(AddFirst) > Limit:
            raise CreoFormat("Creo compression output exceeds its declaration")
        Output.extend(reversed(Stack))
        if AddFirst:
            Output.append(FirstByte)
        if Previous is not None and len(Prefixes) < (1 << MaxBits):
            Prefixes.append(Previous)
            LastBytes.append(FirstByte)
        Previous = min(CodeValue, len(Prefixes) - 1)
        if len(Prefixes) >= (1 << CodeSize) and CodeSize < MaxBits:
            Position, BitBuffer, BitCount = SkipGroup(
                Position, BitBuffer, BitCount, GroupCount, CodeSize, DataValue
            )
            CodeSize += 1
            GroupCount = 0
    return bytes(Output)


def ReadSection(DataValue: bytes, EntryValue: CreoEntry) -> bytes:
    RawData = DataValue[EntryValue.offset : EntryValue.offset + EntryValue.length]
    LineEnd = RawData.find(b"\n")
    if LineEnd < 0:
        raise CreoFormat(f"Creo section {EntryValue.name!r} has no header line")
    BodyData = RawData[LineEnd + 1 :]
    if BodyData.startswith(b"\x1f\x9d"):
        Inflated = Uncompress(BodyData, EntryValue.expanded)
        if EntryValue.expanded > 0 and len(Inflated) != EntryValue.expanded:
            raise CreoFormat(
                f"Creo section {EntryValue.name!r} expanded size does not match"
            )
        return Inflated
    return BodyData
