"""CATIA OSMX object-graph attribute extractor.

The OSMX stream of a natively modelled CATPart is:

    OSMX <header> <object graph> |\\x02 <u32 section_length> <symbol table>

The object graph is a tree of records framed as `7c <subtag> <u32 length>`. The
subtags are 0x02 (symbol table), 0x04 (part container), 0x05 (object), 0x06
(object header), 0x07 (attribute block), 0x08 (relation set), 0x09 (relation),
0x0a (relation operand list), 0x0b (root list), and 0x0c (file header).

A `7c 07` attribute block is a sequence of attributes. Each attribute is a
symbol index followed by a list of tagged values and terminated by `fe`. The
value tags are:

    0x80 <i32>   escape, full 32-bit little-endian int follows
    0x81..0xd0   compact int, value = byte - 0x81 (0..79)
    0xd1..0xe4   two-byte compact int, value = (byte - 0xd1) << 8 | next byte
    0xe6 <f64>   double
    0xe8 <3>     object reference
    0xe9 <4>     object reference
    0xfe         terminator

`CATBmxStream::ReadInt` (`CATOmx.dll` `0x1800016e0`) decodes the compact int with
`Min = 0x80`, `Max = 0x51`, and `Extra = 0x14`: a byte equal to `Min` escapes to a
full int, `1..Max-1` is a one-byte value, and `Max..Max+Extra-1` reads one more
byte. `CATSpecNewStream::ReadInt` (`CATObjectSpecsModeler.dll` `0x18010f200`)
passes exactly those three constants, and `CATOsmObjStream::ReadSpecAttribute`
(`0x1800d9c90`) passes `0x80`, `0x51`, and `0x14` to it.

The symbol index resolves against the symbol table to the attribute name, so the
extractor recovers the feature tree: which attributes each object carries
(`Pocket`, `Shaft`, `EndLimit`, `StartLimit`, `Profile`, `Direction`,
`FirstAngle`, `SecondAngle`, `d_dia`, `p_pitch`, `n_nom_Slot_Width`, ...).

The literal dimension values are not in the attribute block. A dimension
attribute references a parameter object, and the parameter object holds the
value. Decoding the parameter objects is the next step.

Recovered from `CATObjectSpecsModeler.dll`:

- `CATOsmObjStream::ReadOsmValue` at `0x1800d9880`
- `CATOsmObjStream::ReadSpecAttribute` at `0x1800d9c90`
- `CATSpecNewStream::ReadInt` at `0x18010f200`
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "src"))

from convert.adapters.catia.Container import CfvTwoArchive, OsmxArchive

KValueTags = {
    0x80: 5,
    0x81: 1,
    0x82: 2,
    0x83: 2,
    0x84: 2,
    0x85: 2,
    0x86: 2,
    0x87: 2,
    0x8B: 2,
    0x8C: 2,
    0x90: 2,
    0xD8: 2,
    0xD9: 2,
    0xDA: 2,
    0xDB: 2,
    0xDC: 2,
    0xDD: 2,
    0xDE: 2,
    0xDF: 2,
    0xE6: 9,
    0xE8: 4,
    0xE9: 5,
    0xEA: 5,
}


def FindOsmx(Archive: CfvTwoArchive) -> tuple[bytes, OsmxArchive] | None:
    Best: tuple[bytes, OsmxArchive] | None = None
    for Folder in [Archive.outer] + list(Archive.nested):
        for Stream in Folder.streams:
            try:
                Data = Archive.stream_bytes(Stream, Folder)
            except Exception:
                continue
            if not Data.startswith(b"OSMX"):
                continue
            try:
                Parsed = OsmxArchive.from_bytes(Data)
            except Exception:
                continue
            if Best is None or len(Parsed.symbols) > len(Best[1].symbols):
                Best = (Data, Parsed)
    return Best


def AllSymbols(Archive: CfvTwoArchive) -> list[str]:
    Values: list[str] = []
    for Folder in [Archive.outer] + list(Archive.nested):
        for Stream in Folder.streams:
            try:
                Data = Archive.stream_bytes(Stream, Folder)
            except Exception:
                continue
            if not Data.startswith(b"OSMX"):
                continue
            try:
                Parsed = OsmxArchive.from_bytes(Data)
            except Exception:
                continue
            Values.extend(Symbol.value for Symbol in Parsed.symbols)
    return Values


def ParseRecords(Data: bytes, Start: int, End: int) -> list[tuple[int, int, int]]:
    Records: list[tuple[int, int, int]] = []
    Cursor = Start
    while Cursor + 6 <= End:
        if Data[Cursor] != 0x7C:
            Cursor += 1
            continue
        Subtag = Data[Cursor + 1]
        Length = struct.unpack_from("<I", Data, Cursor + 2)[0]
        if Length < 6 or Cursor + Length > End:
            Cursor += 1
            continue
        Records.append((Subtag, Cursor, Length))
        Records.extend(ParseRecords(Data, Cursor + 6, Cursor + Length))
        Cursor += Length
    return Records


KBmxMin = 0x80


def ReadPackInt(Data: bytes, Cursor: int, End: int) -> tuple[int | None, int]:
    """Decode the CATBmxStream::ReadInt compact integer."""
    if Cursor >= End:
        return (None, Cursor)
    Delta = Data[Cursor] - KBmxMin
    if Delta == 0:
        if Cursor + 5 > End:
            return (None, Cursor)
        return (struct.unpack_from("<i", Data, Cursor + 1)[0], Cursor + 5)
    if 1 <= Delta <= 0x50:
        return (Delta - 1, Cursor + 1)
    if 0x51 <= Delta < 0x65:
        if Cursor + 2 > End:
            return (None, Cursor)
        return (((Delta - 0x51) << 8) + Data[Cursor + 1], Cursor + 2)
    return (None, Cursor)


def ParseValues(Data: bytes, Cursor: int, End: int) -> tuple[list[tuple[str, object]], int]:
    Values: list[tuple[str, object]] = []
    while Cursor < End and Data[Cursor] != 0xFE:
        Tag = Data[Cursor]
        Compact, AfterCompact = ReadPackInt(Data, Cursor, End)
        if Compact is not None and Tag not in (0xE6, 0xE8, 0xE9):
            Values.append(("int", Compact))
            Cursor = AfterCompact
            continue
        Width = KValueTags.get(Tag)
        if Width is None:
            Values.append(("byte", Tag))
            Cursor += 1
            continue
        if Cursor + Width > End:
            break
        if Tag == 0x80:
            Values.append(("u32", struct.unpack_from("<I", Data, Cursor + 1)[0]))
        elif Tag == 0x81:
            Values.append(("bool", True))
        elif Tag == 0xE6:
            Values.append(("double", struct.unpack_from("<d", Data, Cursor + 1)[0]))
        elif Tag == 0xE8:
            Values.append(("ref3", Data[Cursor + 1 : Cursor + 4].hex()))
        elif Tag == 0xE9:
            Values.append(("ref4", Data[Cursor + 1 : Cursor + 5].hex()))
        elif Tag == 0xEA:
            Values.append(("int32", struct.unpack_from("<i", Data, Cursor + 1)[0]))
        else:
            Values.append(("small", Data[Cursor + 1]))
        Cursor += Width
    return Values, Cursor


def ParseAttributes(
    Data: bytes, Start: int, Length: int, Symbols: list[str]
) -> list[tuple[str, list[tuple[str, object]]]]:
    Attributes: list[tuple[str, list[tuple[str, object]]]] = []
    Cursor = Start + 6
    End = Start + Length
    while Cursor < End:
        Key = Data[Cursor]
        if Key == 0xFE:
            Cursor += 1
            continue
        Cursor += 1
        Values, Cursor = ParseValues(Data, Cursor, End)
        if Cursor < End and Data[Cursor] == 0xFE:
            Cursor += 1
        Name = Symbols[Key] if Key < len(Symbols) else f"?{Key}"
        Attributes.append((Name, Values))
    return Attributes


def ObjectId(Segment: bytes) -> int:
    Marker = Segment.find(b"\x7c\x06")
    if Marker < 0:
        return -1
    Length = struct.unpack_from("<I", Segment, Marker + 2)[0]
    Header = Segment[Marker + 6 : Marker + Length]
    Cursor = Header.find(b"\xea")
    if Cursor < 0 or Cursor + 5 > len(Header):
        return -1
    return struct.unpack_from("<I", Header, Cursor + 1)[0]


def WalkBlock(Data: bytes, Start: int, Length: int) -> tuple[list[int], int, int]:
    """Walk one 7c07 attribute block and return (keys, cursor, end)."""
    Cursor = Start + 6
    End = Start + Length
    Keys: list[int] = []
    while Cursor < End:
        if Data[Cursor] == 0xFE:
            Cursor += 1
            continue
        Keys.append(Data[Cursor])
        Cursor += 1
        while Cursor < End and Data[Cursor] != 0xFE:
            Tag = Data[Cursor]
            if Tag == 0xE6:
                Cursor += 9
            elif Tag == 0xE8:
                Cursor += 4
            elif Tag == 0xE9:
                Cursor += 5
            else:
                Value, After = ReadPackInt(Data, Cursor, End)
                Cursor = After if Value is not None else Cursor + 1
        if Cursor < End and Data[Cursor] == 0xFE:
            Cursor += 1
    return (Keys, Cursor, End)


def WalkStats(PathValue: Path) -> tuple[int, int, int]:
    """Count attribute blocks whose single-byte key walk closes cleanly."""
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = FindOsmx(Archive)
    if Found is None:
        return (0, 0, 0)
    Data, Parsed = Found
    Symbols = [Symbol.value for Symbol in Parsed.symbols]
    Total = 0
    Clean = 0
    OutOfRange = 0
    for Subtag, Start, Length in ParseRecords(Data, 104, Parsed.symbol_table_offset):
        if Subtag != 0x07:
            continue
        Total += 1
        Keys, Cursor, End = WalkBlock(Data, Start, Length)
        if Cursor != End or any(Key >= len(Symbols) for Key in Keys):
            OutOfRange += 1
            continue
        Clean += 1
    return (Total, Clean, OutOfRange)


def ExtractObjects(PathValue: Path) -> list[tuple[int, list[float]]]:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = FindOsmx(Archive)
    if Found is None:
        return []
    Data, Parsed = Found
    Values: list[tuple[int, list[float]]] = []
    for Subtag, Start, Length in ParseRecords(Data, 104, Parsed.symbol_table_offset):
        if Subtag != 0x05:
            continue
        Segment = Data[Start : Start + Length]
        Doubles: list[float] = []
        for Offset in range(len(Segment) - 9):
            if Segment[Offset] != 0xE6:
                continue
            Value = struct.unpack_from("<d", Segment, Offset + 1)[0]
            if 0.001 <= abs(Value) <= 1e6 and abs(Value - round(Value, 6)) < 1e-6:
                Doubles.append(round(Value, 4))
        if Doubles:
            Values.append((ObjectId(Segment), Doubles))
    return Values


def Extract(PathValue: Path) -> tuple[list[str], dict[str, int]]:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = FindOsmx(Archive)
    if Found is None:
        return ([], {})
    Data, Parsed = Found
    Symbols = [Symbol.value for Symbol in Parsed.symbols]
    Records = ParseRecords(Data, 104, Parsed.symbol_table_offset)
    Highest = 0
    for Subtag, Start, Length in Records:
        if Subtag != 0x07:
            continue
        Cursor = Start + 6
        End = Start + Length
        while Cursor < End:
            Key = Data[Cursor]
            if Key == 0xFE:
                Cursor += 1
                continue
            Highest = max(Highest, Key)
            Cursor += 1
            _, Cursor = ParseValues(Data, Cursor, End)
            if Cursor < End and Data[Cursor] == 0xFE:
                Cursor += 1
    if Highest >= len(Symbols):
        Symbols = AllSymbols(Archive)
    Names: list[str] = []
    Counts: dict[str, int] = {}
    for Subtag, Start, Length in Records:
        if Subtag != 0x07:
            continue
        for Name, _ in ParseAttributes(Data, Start, Length, Symbols):
            Names.append(Name)
            Counts[Name] = Counts.get(Name, 0) + 1
    return (Names, Counts)


def ExtractValues(PathValue: Path) -> list[float]:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = FindOsmx(Archive)
    if Found is None:
        return []
    Data, Parsed = Found
    Values: list[float] = []
    for Offset in range(104, Parsed.symbol_table_offset - 9):
        if Data[Offset] != 0xE6:
            continue
        Value = struct.unpack_from("<d", Data, Offset + 1)[0]
        if 0.001 <= abs(Value) <= 1e6 and abs(Value - round(Value, 6)) < 1e-6:
            Values.append(Value)
    return Values


def Main() -> None:
    Base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("re/catia/examples/parametric")
    for PathValue in sorted(Base.rglob("*.CATPart")):
        if not PathValue.is_file():
            continue
        Names, Counts = Extract(PathValue)
        Values = ExtractValues(PathValue)
        Top = sorted(Counts.items(), key=lambda Item: -Item[1])[:10]
        print(f"{PathValue.name:56s} attributes={len(Names):5d} distinct={len(Counts):4d}")
        print(f"  {Top}")
        print(f"  doubles={len(Values)} {sorted(set(round(V, 4) for V in Values))[:12]}")
        print(f"  objects={ExtractObjects(PathValue)[:8]}")
        Total, Clean, Bad = WalkStats(PathValue)
        print(f"  blocks={Total} clean={Clean} exceptions={Bad}")


if __name__ == "__main__":
    Main()
