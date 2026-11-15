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
    Section = Sections[int(ArgValues[1]) if len(ArgValues) > 1 else 0]
    Start = Section.Offset
    End = Section.Offset + Section.Length
    Cursor = Start
    while Cursor + 2 <= End:
        Length = struct.unpack_from("<H", DataValue, Cursor)[0]
        if 1 <= Length <= 64 and Cursor + 2 + Length <= End:
            Text = DataValue[Cursor + 2 : Cursor + 2 + Length]
            if all(0x20 <= Byte < 0x7F for Byte in Text):
                print(f"{Cursor:06x} len={Length:3d} {Text.decode('ascii')}")
                Cursor += 2 + Length
                continue
        Cursor += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
