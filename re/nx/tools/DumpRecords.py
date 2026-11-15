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


def Hex(DataValue: bytes) -> str:
    return " ".join(f"{Item:02x}" for Item in DataValue)


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) < 2:
        print("usage: DumpRecords.py <part.prt> <offset> [<offset> ...]")
        return 2
    DataValue = Payload(ArgValues[0])
    for Text in ArgValues[1:]:
        Offset = int(Text, 0)
        print(f"== {Text} ==")
        for Row in range(0, 64, 16):
            Chunk = DataValue[Offset + Row : Offset + Row + 16]
            if not Chunk:
                break
            print(f"{Offset + Row:06x}  {Hex(Chunk)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
