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


def FailRowMut(Strict: bool, Notes: list[str], Message: str) -> None:
    if Strict:
        raise CreoFormat(Message)
    Notes.append(Message)


def ReadRows(
    DataValue: bytes, Start: int, Count: int, Width: int
) -> tuple[list[list[str]], int]:
    RowList: list[list[str]] = []
    Position = Start
    for _ in range(Count):
        EndValue = Position + Width
        if EndValue > len(DataValue):
            raise CreoFormat("Creo table of contents is truncated")
        RowText = DataValue[Position:EndValue].decode("latin-1")
        Words = RowText.rstrip("#\r\n").split()
        RowList.append(Words)
        Position = EndValue
    return RowList, Position


def MakeEntry(
    NameText: str,
    Absolute: int,
    LengthValue: int,
    ExpandedValue: int,
    RowValue: list[str],
) -> CreoEntry:
    KindText = RowValue[5] if len(RowValue) > 5 else ""
    ChecksumA = ParseHex(RowValue[7]) if len(RowValue) > 7 else 0
    ChecksumB = ParseHex(RowValue[8]) if len(RowValue) > 8 else 0
    return CreoEntry(
        name=NameText,
        offset=Absolute,
        length=LengthValue,
        expanded=ExpandedValue,
        kind=KindText,
        checksum_a=ChecksumA or 0,
        checksum_b=ChecksumB or 0,
    )


def ReadEntry(
    RowValue: list[str],
    BaseValue: int,
    DataValue: bytes,
    Strict: bool,
    Notes: list[str],
) -> tuple[CreoEntry | None, int | None]:
    if not RowValue:
        return (None, None)
    NameText = RowValue[0]
    if len(RowValue) < 4:
        FailRowMut(Strict, Notes, f"Creo table row {NameText!r} is incomplete")
        return (None, None)
    OffsetValue = ParseHex(RowValue[1])
    LengthValue = ParseHex(RowValue[2])
    ExpandedValue = ParseHex(RowValue[3])
    if OffsetValue is None or LengthValue is None or ExpandedValue is None:
        FailRowMut(Strict, Notes, f"Creo table row {NameText!r} has invalid numbers")
        return (None, None)
    Absolute = BaseValue + OffsetValue
    if NameText == "NEXT_TOC_ENTRY":
        return (None, Absolute)
    Expected = b"#" + NameText.encode("latin-1") + b"\n"
    if (
        Absolute < 0
        or LengthValue < len(Expected)
        or Absolute + LengthValue > len(DataValue)
        or not DataValue.startswith(Expected, Absolute)
    ):
        FailRowMut(Strict, Notes, f"Creo table row {NameText!r} has an invalid extent")
        return (None, None)
    return (MakeEntry(NameText, Absolute, LengthValue, ExpandedValue, RowValue), None)


def ReadTable(
    DataValue: bytes,
    Position: int,
    BaseValue: int,
    Strict: bool,
    Notes: list[str],
) -> tuple[list[CreoEntry], int | None]:
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
    RowList, _ = ReadRows(DataValue, LineEnd + 1, CountValue, WidthValue)
    Entries: list[CreoEntry] = []
    NextTable: int | None = None
    for RowValue in RowList:
        EntryValue, NextValue = ReadEntry(RowValue, BaseValue, DataValue, Strict, Notes)
        if EntryValue is not None:
            Entries.append(EntryValue)
        if NextValue is not None:
            NextTable = NextValue
    return (Entries, NextTable)


def ReadToc(DataValue: bytes, BaseValue: int, Strict: bool = True) -> CreoToc:
    Entries: list[CreoEntry] = []
    Notes: list[str] = []
    SeenSet: set[int] = set()
    Position = FindMarker(DataValue, b"#UGC_TOC", BaseValue)
    if Position < 0:
        raise CreoFormat("Creo file has no table of contents")
    while Position not in SeenSet and len(Entries) < KMaxSections:
        SeenSet.add(Position)
        TableEntries, NextTable = ReadTable(
            DataValue, Position, BaseValue, Strict, Notes
        )
        Entries.extend(TableEntries)
        if NextTable is None:
            break
        Found = FindMarker(DataValue, b"#UGC_TOC", max(0, NextTable - 8))
        if Found < 0 or Found > NextTable + 64:
            FailRowMut(Strict, Notes, "Creo continuation table is missing")
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


def ReadBits(
    DataValue: bytes, Position: int, BitBuffer: int, BitCount: int, CodeSize: int
) -> tuple[int, int, int, bool]:
    while BitCount < CodeSize:
        if Position >= len(DataValue):
            return (Position, BitBuffer, BitCount, False)
        BitBuffer |= DataValue[Position] << BitCount
        Position += 1
        BitCount += 8
    return (Position, BitBuffer, BitCount, True)


def SelectCode(
    CodeValue: int, TableSize: int, Previous: int | None
) -> tuple[int, bool]:
    if Previous is None:
        if CodeValue >= TableSize:
            raise CreoFormat("Creo compression first code is invalid")
        return (CodeValue, False)
    if CodeValue < TableSize:
        return (CodeValue, False)
    if CodeValue == TableSize:
        return (Previous, True)
    raise CreoFormat("Creo compression code is outside the table")


def ExpandCode(
    Prefixes: list[int], LastBytes: list[int], EntryCode: int
) -> tuple[bytearray, int]:
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
    return (Stack, FirstByte)


def UpdateDictMut(
    Prefixes: list[int],
    LastBytes: list[int],
    Previous: int | None,
    FirstByte: int,
    MaxBits: int,
) -> None:
    if Previous is not None and len(Prefixes) < (1 << MaxBits):
        Prefixes.append(Previous)
        LastBytes.append(FirstByte)


def ResetBlockMut(
    Prefixes: list[int],
    LastBytes: list[int],
    Position: int,
    BitBuffer: int,
    BitCount: int,
    GroupCount: int,
    CodeSize: int,
    DataValue: bytes,
) -> tuple[int, int, int]:
    del Prefixes[257:]
    del LastBytes[257:]
    return SkipGroup(Position, BitBuffer, BitCount, GroupCount, CodeSize, DataValue)


def InitState(Flags: int) -> tuple[int, bool, list[int], list[int]]:
    MaxBits = Flags & 0x1F
    if MaxBits < 9 or MaxBits > 16:
        raise CreoFormat("Creo compression code width is invalid")
    BlockMode = bool(Flags & 0x80)
    Prefixes = list(range(256))
    LastBytes = list(range(256))
    if BlockMode:
        Prefixes.append(0)
        LastBytes.append(0)
    return (MaxBits, BlockMode, Prefixes, LastBytes)


def DecodeCodeMut(
    CodeValue: int,
    Prefixes: list[int],
    LastBytes: list[int],
    Previous: int | None,
    MaxBits: int,
    Output: bytearray,
    Limit: int,
) -> int | None:
    EntryCode, AddFirst = SelectCode(CodeValue, len(Prefixes), Previous)
    Stack, FirstByte = ExpandCode(Prefixes, LastBytes, EntryCode)
    if len(Output) + len(Stack) + int(AddFirst) > Limit:
        raise CreoFormat("Creo compression output exceeds its declaration")
    Output.extend(reversed(Stack))
    if AddFirst:
        Output.append(FirstByte)
    UpdateDictMut(Prefixes, LastBytes, Previous, FirstByte, MaxBits)
    return min(CodeValue, len(Prefixes) - 1)


def GrowCode(
    Prefixes: list[int],
    Position: int,
    BitBuffer: int,
    BitCount: int,
    GroupCount: int,
    CodeSize: int,
    MaxBits: int,
    DataValue: bytes,
) -> tuple[int, int, int, int, int]:
    if len(Prefixes) >= (1 << CodeSize) and CodeSize < MaxBits:
        Position, BitBuffer, BitCount = SkipGroup(
            Position, BitBuffer, BitCount, GroupCount, CodeSize, DataValue
        )
        CodeSize += 1
        GroupCount = 0
    return (Position, BitBuffer, BitCount, CodeSize, GroupCount)


def Uncompress(DataValue: bytes, Expected: int) -> bytes:
    if len(DataValue) < 4 or DataValue[:2] != b"\x1f\x9d":
        raise CreoFormat("Creo section is not Unix-compressed")
    MaxBits, BlockMode, Prefixes, LastBytes = InitState(DataValue[2])
    Limit = min(max(Expected, 1), KMaxSectionBytes)
    Position = 3
    BitBuffer = 0
    BitCount = 0
    CodeSize = 9
    GroupCount = 0
    Previous: int | None = None
    Output = bytearray()
    while len(Output) < Limit:
        Position, BitBuffer, BitCount, HasBits = ReadBits(
            DataValue, Position, BitBuffer, BitCount, CodeSize
        )
        if not HasBits:
            return bytes(Output)
        CodeValue = BitBuffer & ((1 << CodeSize) - 1)
        BitBuffer >>= CodeSize
        BitCount -= CodeSize
        GroupCount += 1
        if BlockMode and CodeValue == 256:
            Position, BitBuffer, BitCount = ResetBlockMut(
                Prefixes,
                LastBytes,
                Position,
                BitBuffer,
                BitCount,
                GroupCount,
                CodeSize,
                DataValue,
            )
            CodeSize = 9
            GroupCount = 0
            Previous = None
            continue
        Previous = DecodeCodeMut(
            CodeValue, Prefixes, LastBytes, Previous, MaxBits, Output, Limit
        )
        Position, BitBuffer, BitCount, CodeSize, GroupCount = GrowCode(
            Prefixes,
            Position,
            BitBuffer,
            BitCount,
            GroupCount,
            CodeSize,
            MaxBits,
            DataValue,
        )
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
