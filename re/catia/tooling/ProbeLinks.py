"""Probe a CATPart for the CGM linked-object list that carries face surfaces.

`CATCXFace::UnStream` (`CATTopologicalObjects.dll` `0x18054eef0`) takes entry 1 of the
linked-object list as the face surface. The count is written by
`CATMathStreamImpl::WriteULong(value, "#NBLinkObjs")` (`CATMathStream.dll` `0x1800b7bb0`),
whose prefix byte flags the presence of bytes 1, 2, and 3 with bits 0x10, 0x20, and 0x40 and
is followed by one to four little-endian bytes. The array uses the same element form through
`ReadULong(uint*, count, "^LinkObj")`.

This tool decodes a stream with that framing and reports every offset where a run of
count-then-count-entries records is long enough to be a face list, together with the number of
distinct second entries, which is what a pooled part must show (fewer distinct surfaces than
faces). It is a probe, not a decoder: it prints candidates for a controlled corpus to confirm.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")

from convert.adapters.catia.Container import CfvTwoArchive
from convert.adapters.catia.NativeBrep import Largest, ParseBrep, ParseSurfaces


def ReadULong(Data: bytes, Cursor: int) -> tuple[int | None, int]:
    """Decode one CATMathStream ULong."""
    if Cursor >= len(Data):
        return (None, Cursor)
    Prefix = Data[Cursor]
    Cursor += 1
    Width = 1 + (((Prefix >> 4) & 1) + ((Prefix >> 5) & 1) + ((Prefix >> 6) & 1))
    if Cursor + Width > len(Data):
        return (None, Cursor)
    return (int.from_bytes(Data[Cursor : Cursor + Width], "little"), Cursor + Width)


def Runs(Data: bytes, Minimum: int) -> list[tuple[int, int, int]]:
    """Return (records, offset, distinct second entries) for long candidate runs."""
    Found: list[tuple[int, int, int]] = []
    for Start in range(len(Data) - 20):
        Cursor = Start
        Records: list[list[int]] = []
        while len(Records) < 200 and Cursor < len(Data):
            Count, After = ReadULong(Data, Cursor)
            if Count is None or not 2 <= Count <= 6:
                break
            Tags: list[int] = []
            Position = After
            Broken = False
            for _ in range(Count):
                Value, Position = ReadULong(Data, Position)
                if Value is None:
                    Broken = True
                    break
                Tags.append(Value)
            if Broken:
                break
            Records.append(Tags)
            Cursor = Position
        if len(Records) >= Minimum:
            Seconds = {Value[1] for Value in Records if len(Value) > 1}
            Found.append((len(Records), Start, len(Seconds)))
    Found.sort(key=lambda Value: -Value[0])
    return Found[:8]


def Probe(PathValue: Path) -> None:
    Archive = CfvTwoArchive.from_bytes(PathValue.read_bytes())
    Folder = Archive.nested[0]
    MainData = Archive.stream_bytes(Largest(Folder, "MainDataStream"), Folder)
    Pool = len(ParseSurfaces(Archive.stream_bytes(Largest(Folder, "SurfacicReps"), Folder)))
    Parsed = ParseBrep(Archive)
    Faces = len(Parsed.trims)
    print(f"{PathValue.name}: faces {Faces} pool {Pool} main {len(MainData)}")
    for Records, Offset, Distinct in Runs(MainData, max(10, Faces // 2)):
        print(f"  run records {Records:4d} at {Offset:6d} distinct-second {Distinct}")


def Main() -> None:
    Base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("re/catia/examples/.CATPart")
    for PathValue in sorted(Base.rglob("*.CATPart")):
        try:
            Probe(PathValue)
        except (IndexError, KeyError, ValueError) as ErrorInfo:
            print(f"{PathValue.name}: probe failed: {ErrorInfo}")


if __name__ == "__main__":
    Main()
