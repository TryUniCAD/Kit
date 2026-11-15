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
    print("section0", hex(Start), hex(End), "len", Section.Length)
    # find monotone u32 runs starting with 0
    Hits = []
    for Offset in range(Start, End - 8, 4):
        if struct.unpack_from("<I", DataValue, Offset)[0] != 0:
            continue
        Run = [0]
        Cursor = Offset + 4
        while Cursor + 4 <= End:
            Value = struct.unpack_from("<I", DataValue, Cursor)[0]
            if Value <= Run[-1]:
                break
            Run.append(Value)
            Cursor += 4
        if len(Run) >= 4:
            Count = struct.unpack_from("<I", DataValue, Cursor)[0] if Cursor + 4 <= End else None
            Hits.append((Offset, len(Run), Cursor, Count, Run[:6], Run[-3:]))
    print("hits", len(Hits))
    for Offset, Length, Cursor, Count, Head, Tail in Hits[:40]:
        print(
            f"{Offset:06x} run={Length:4d} end={Cursor:06x} next={Count} head={Head} tail={Tail}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
