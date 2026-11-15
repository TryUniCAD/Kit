"""List the object graph of a CATProduct: class, part, and instance symbols.

A product OSMX object is `7c 05 <u32 length>` containing `7c 06 <u32 length>` whose header is

    <flag0> <flag1> <symbolA> <symbolB> ea <u32 object number> ...

`symbolA` and `symbolB` resolve against the OSMX symbol table and carry the part and instance names:
on `Brake_Pedal_Assembly - Backup 1.CATProduct` an instance object reads
`00 04 45 46 ea 03 ...` with `symbolA = Washer_5_DIN_433_1.2` and
`symbolB = Washer_5_DIN_433_1.3`. The second symbol byte of the flags is the class:
`04` is `ASMPRODUCT`, `00` is `CATCatalogManager`, `09` is `A.1`/`_Component`.

Instance placement shows up in the same object as `0xe6` doubles.

Usage: uv run python re/catia/tooling/ProductGraph.py [file or directory]
"""

from __future__ import annotations

import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/catia/tooling")

from convert.adapters.catia.Parametric import OsmxStream, ReadRecords

from convert.adapters.catia.Container import CfvTwoArchive


def Rows(PathValue: Path) -> list[tuple[int, str, str, str, int]]:
    """Return (object number, class, symbolA, symbolB, length) for every product object."""
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Found = OsmxStream(Archive)
    if Found is None:
        return []
    Data, Parsed = Found
    Symbols = [Symbol.value for Symbol in Parsed.symbols]
    RowsOut: list[tuple[int, str, str, str, int]] = []
    for Subtag, Start, Length in ReadRecords(Data, 104, Parsed.symbol_table_offset):
        if Subtag != 0x05:
            continue
        Child = Data.find(b"\x7c\x06", Start + 6, Start + Length)
        if Child < 0:
            continue
        InnerLength = struct.unpack_from("<I", Data, Child + 2)[0]
        Header = Data[Child + 6 : Child + InnerLength]
        Marker = Header.find(b"\xea")
        if Marker < 0:
            continue
        Number = struct.unpack_from("<I", Header, Marker + 1)[0]
        Flags = Header[:Marker]
        if len(Flags) < 4:
            continue
        Names = [
            Symbols[Value] if Value < len(Symbols) else f"?{Value}" for Value in Flags
        ]
        RowsOut.append((Number, Names[1], Names[2], Names[3], Length))
    return RowsOut


def Main() -> None:
    """Print the product graph of every given CATProduct."""
    Base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("re/catia/examples/.CATProduct")
    Paths = [Base] if Base.is_file() else sorted(Base.rglob("*.CATProduct"))
    for PathValue in Paths:
        RowsOut = Rows(PathValue)
        print(f"=== {PathValue.name}: {len(RowsOut)} objects")
        for Row in RowsOut:
            print(f"  obj {Row[0]:4d} class {Row[1]:14s} part {Row[2]:26s} instance {Row[3]:26s} len {Row[4]}")
        Classes = Counter(Row[1] for Row in RowsOut)
        print(f"  classes {dict(Classes)}")


if __name__ == "__main__":
    Main()
