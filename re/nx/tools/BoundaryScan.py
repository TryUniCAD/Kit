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
    for SectionIndex, Section in enumerate(Sections):
        Start = Section.Offset
        End = Section.Offset + Section.Length
        print("section", SectionIndex, hex(Start), hex(End), "counts", Section.Counts)
        Hits = []
        for Offset in range(Start, End - 8, 4):
            Run = [struct.unpack_from("<I", DataValue, Offset)[0]]
            Cursor = Offset + 4
            while Cursor + 4 <= End:
                Value = struct.unpack_from("<I", DataValue, Cursor)[0]
                if Value <= Run[-1]:
                    break
                Run.append(Value)
                Cursor += 4
            if len(Run) < 4:
                continue
            if Cursor + 4 > End:
                continue
            Count = struct.unpack_from("<I", DataValue, Cursor)[0]
            if Count != len(Run) - 1:
                continue
            IdsAt = Cursor + 4
            if IdsAt + 4 * Count > End:
                continue
            Ids = [
                struct.unpack_from("<I", DataValue, IdsAt + 4 * Index)[0]
                for Index in range(min(Count, 6))
            ]
            Hits.append((Offset, len(Run), Cursor, Count, Run[:4], Run[-3:], Ids))
        print("  boundary+count hits", len(Hits))
        for Offset, Length, Cursor, Count, Head, Tail, Ids in Hits[:20]:
            print(
                f"  {Offset:06x} run={Length:4d} count_at={Cursor:06x} count={Count} head={Head} tail={Tail} ids={Ids}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
