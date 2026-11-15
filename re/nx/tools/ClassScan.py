from __future__ import annotations
import sys
from pathlib import Path

from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams
from convert.adapters.nx.LegacyClasses import LegacyStart, ReadFrame


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
    Start = LegacyStart(DataValue)
    print("start", hex(Start))
    Cursor = Start
    Index = 0
    while Cursor < len(DataValue):
        Frame = ReadFrame(DataValue, Cursor)
        if Frame is None:
            print("stop at", hex(Cursor), "byte", hex(DataValue[Cursor]))
            break
        Record, Next = Frame
        if Index >= 90:
            print(
                Index,
                hex(Cursor),
                Record.Schema,
                Record.SchemaFlag,
                Record.Name,
                hex(Record.Value),
            )
        Index += 1
        Cursor = Next
    print("frames", Index, "end", hex(Cursor))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
