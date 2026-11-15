from __future__ import annotations
import struct
import sys
from pathlib import Path

from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams
from convert.adapters.nx.LegacyClasses import (
    ClassTableEnd,
    LegacyAttrs,
    LegacyTable,
)
from convert.adapters.nx.LegacySection import ReadSections


def Payload(PathValue: str) -> bytes:
    DataValue = Path(PathValue).read_bytes()
    FileValue = ReadCompound(DataValue)
    Streams = {Stream.path: Stream.data for Stream in ReadStreams(FileValue)}
    for Key, Value in Streams.items():
        if Key.endswith("UG_PART") or Key == "UG_PART":
            return Value
    raise SystemExit(f"no UG_PART stream in {list(Streams)}")


def Main(ArgValues: list[str]) -> int:
    DataValue = Payload(ArgValues[0])
    Sections = ReadSections(DataValue)
    print("sections", len(Sections))
    for Index, Section in enumerate(Sections):
        print(
            "section",
            Index,
            "at",
            hex(Section.Offset),
            "len",
            Section.Length,
            "ver",
            Section.Version,
            "counts",
            Section.Counts,
        )
    Records = LegacyTable(DataValue)
    Attrs = LegacyAttrs(DataValue)
    End = ClassTableEnd(DataValue, Records)
    print("classes", len(Records), "attrs", len(Attrs), "class_end", hex(End))
    # dump bytes after the class table
    for Row in range(0, 96, 16):
        Chunk = DataValue[End + Row : End + Row + 16]
        if not Chunk:
            break
        print(f"{End + Row:06x}  {' '.join(f'{Item:02x}' for Item in Chunk)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
