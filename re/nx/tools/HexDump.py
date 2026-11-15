from __future__ import annotations
import struct
import sys
from pathlib import Path

from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams
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
    Section = Sections[0]
    Start = Section.Offset
    End = Section.Offset + Section.Length
    Cursor = int(ArgValues[1], 0)
    Limit = int(ArgValues[2], 0) if len(ArgValues) > 2 else End
    while Cursor < Limit:
        Line = DataValue[Cursor : Cursor + 16]
        Text = "".join(chr(Byte) if 32 <= Byte < 127 else "." for Byte in Line)
        Hex = " ".join(f"{Byte:02x}" for Byte in Line)
        print(f"{Cursor:06x}  {Hex:<47}  {Text}")
        Cursor += 16
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
