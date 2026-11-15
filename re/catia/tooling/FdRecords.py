"""Dump the three `30 04 04 fd ff` records that every CATPart carries.

Two of the three records share one layout while the third differs:

    r0  marker 30 04 04 fd ff | 00 00 00 01 | 00 | five f32 | kind u32 | 13-byte tail
    r1  r0 followed by 95 ff <u16> 00 00 00
    r2  marker | ... | ff ff 02 00 01 ... (a different shape)

`kind` is 3 for r0 and 19 for r1 in every file measured, and the five floats vary per part.
The u16 in r1 equals `(MainDataStream length - 199) mod 65536` for 26 of the 27 corpus parts;
`Pedal_Body` is off by 340.

Usage: uv run python re/catia/tooling/FdRecords.py [directory]
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, "src")

from convert.adapters.catia.Container import CfvTwoArchive
from convert.adapters.catia.NativeBrep import Largest

KMarker = b"\x30\x04\x04\xfd\xff"


def Records(Data: bytes) -> list[int]:
    """Return the offsets of every fd record."""
    Offsets: list[int] = []
    Cursor = 0
    while True:
        Found = Data.find(KMarker, Cursor)
        if Found < 0:
            return Offsets
        Offsets.append(Found)
        Cursor = Found + 1


def Describe(PathValue: Path) -> None:
    """Print one part's fd records and the length relation."""
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Folder = Archive.nested[0]
    MainData = Archive.stream_bytes(Largest(Folder, "MainDataStream"), Folder)
    Offsets = Records(MainData)
    print(f"{PathValue.name}: main {len(MainData)} records {Offsets}")
    for Index, Offset in enumerate(Offsets):
        Floats = struct.unpack_from("<5f", MainData, Offset + 10)
        Kind = struct.unpack_from("<I", MainData, Offset + 30)[0]
        Span = (Offsets[Index + 1] if Index + 1 < len(Offsets) else len(MainData)) - Offset
        print(f"  r{Index} at {Offset:6d} span {Span:3d} kind {Kind:3d} floats "
              f"{[round(Value, 4) for Value in Floats]}")
    if len(Offsets) > 1:
        Tail = MainData[Offsets[1] : Offsets[1] + 80]
        Marker = Tail.find(b"\x95\xff", 30)
        if Marker >= 0:
            Value = int.from_bytes(Tail[Marker + 2 : Marker + 4], "little")
            Expected = (len(MainData) - 199) % 65536
            print(f"  r1 u16 {Value} expected {Expected} match {Value == Expected}")


def Main() -> None:
    """Describe every part under the given directory."""
    Base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("re/catia/examples/.CATPart")
    for PathValue in sorted(Base.rglob("*.CATPart")):
        Describe(PathValue)


if __name__ == "__main__":
    Main()
