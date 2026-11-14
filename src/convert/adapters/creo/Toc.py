from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.creo.Compress import Uncompress
from convert.adapters.creo.CreoFormat import CreoFormat

KMaxSections = 100000


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
