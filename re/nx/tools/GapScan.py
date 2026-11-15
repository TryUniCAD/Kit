from __future__ import annotations
import struct
import sys
from pathlib import Path

from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams


def Payload(PathValue: str) -> bytes:
    DataValue = Path(PathValue).read_bytes()
    FileValue = ReadCompound(DataValue)
    Streams = {Stream.path: Stream.data for Stream in ReadStreams(FileValue)}
    for Key, Value in Streams.items():
        if Key.endswith("UG_PART") or Key == "UG_PART":
            return Value
    raise SystemExit(f"no UG_PART stream in {list(Streams)}")


def Strings(DataValue: bytes) -> list[tuple[int, int, str]]:
    Output = []
    Position = 0
    while Position + 5 <= len(DataValue):
        if DataValue[Position] == 3:
            Length = struct.unpack_from("<I", DataValue, Position + 1)[0]
            if 2 <= Length <= 200 and Position + 5 + Length <= len(DataValue):
                Text = DataValue[Position + 5 : Position + 5 + Length]
                if Text.endswith(b"\0") and all(32 <= Item < 127 for Item in Text[:-1]):
                    Output.append((Position, Length, Text[:-1].decode("ascii")))
                    Position += 5 + Length
                    continue
        Position += 1
    return Output


def Main(ArgValues: list[str]) -> int:
    DataValue = Payload(ArgValues[0])
    Found = Strings(DataValue)
    print("strings", len(Found))
    for Index in range(len(Found) - 1):
        Start, Length, Text = Found[Index]
        NextStart = Found[Index + 1][0]
        GapStart = Start + 5 + Length
        Gap = NextStart - GapStart
        if Gap > 0:
            Head = DataValue[GapStart : GapStart + min(Gap, 24)]
            print(f"{GapStart:06x} gap {Gap:3d}  {Head.hex(' ')}  -> {Text!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
