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

    0x80 <u32>   object reference or float bits
    0x81         boolean true
    0xe8 <3>     object reference
    0xe9 <4>     object reference
    0xfe         terminator

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


def ParseValues(Data: bytes, Cursor: int, End: int) -> tuple[list[tuple[str, object]], int]:
    Values: list[tuple[str, object]] = []
    while Cursor < End and Data[Cursor] != 0xFE:
        Tag = Data[Cursor]
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


def ExtractValues(PathValue: Path) -> list[tuple[str, float]]:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = FindOsmx(Archive)
    if Found is None:
        return []
    Data, Parsed = Found
    Symbols = [Symbol.value for Symbol in Parsed.symbols]
    Records = ParseRecords(Data, 104, Parsed.symbol_table_offset)
    Highest = max(
        (Data[Start + 6] for Subtag, Start, _ in Records if Subtag == 0x07),
        default=0,
    )
    if Highest >= len(Symbols):
        Symbols = AllSymbols(Archive)
    Values: list[tuple[str, float]] = []
    for Subtag, Start, Length in Records:
        if Subtag != 0x07:
            continue
        for Name, Items in ParseAttributes(Data, Start, Length, Symbols):
            for Kind, Value in Items:
                if Kind == "double" and isinstance(Value, float):
                    Values.append((Name, Value))
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
        print(f"  doubles={len(Values)} {Values[:8]}")


if __name__ == "__main__":
    Main()
