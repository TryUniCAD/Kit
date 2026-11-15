from __future__ import annotations
import struct
import sys
from pathlib import Path

from convert.adapters.nx.CompoundReader import ReadCompound, ReadStreams
from convert.adapters.nx.LegacyClasses import ClassTableEnd, LegacyTable
from convert.adapters.nx.LegacySection import ReadSections


def Payload(PathValue: str) -> bytes:
    DataValue = Path(PathValue).read_bytes()
    FileValue = ReadCompound(DataValue)
    Streams = {Stream.path: Stream.data for Stream in ReadStreams(FileValue)}
    for Key, Value in Streams.items():
        if Key.endswith("UG_PART") or Key == "UG_PART":
            return Value
    raise SystemExit(f"no UG_PART stream in {list(Streams)}")


def Bare(DataValue: bytes, Cursor: int, End: int) -> tuple[str, int] | None:
    Start = Cursor
    while Cursor < End and 0x20 <= DataValue[Cursor] < 0x7F:
        Cursor += 1
    if Cursor == Start:
        return None
    return (DataValue[Start:Cursor].decode("ascii"), Cursor)


def Main(ArgValues: list[str]) -> int:
    DataValue = Payload(ArgValues[0])
    Records = LegacyTable(DataValue)
    Cursor = ClassTableEnd(DataValue, Records)
    Section = ReadSections(DataValue)[0]
    End = Section.Offset + Section.Length
    print("field registry start", hex(Cursor), "section end", hex(End))
    Count = 0
    while Cursor < End:
        Name = Bare(DataValue, Cursor, End)
        if Name is None:
            print("stop at", hex(Cursor), "byte", hex(DataValue[Cursor]))
            break
        FieldName, Cursor = Name
        if Cursor + 4 + 1 + 2 > End:
            print("truncated after", FieldName)
            break
        FieldId = struct.unpack_from("<I", DataValue, Cursor)[0]
        Cursor += 4
        Tag = DataValue[Cursor]
        Cursor += 1
        SchemaLength = struct.unpack_from("<H", DataValue, Cursor)[0]
        Cursor += 2
        Schema = DataValue[Cursor : Cursor + SchemaLength].decode("ascii", "replace")
        Cursor += SchemaLength
        SchemaId = struct.unpack_from("<I", DataValue, Cursor)[0]
        Cursor += 4
        ClassLength = struct.unpack_from("<H", DataValue, Cursor)[0]
        Cursor += 2
        ClassName = DataValue[Cursor : Cursor + ClassLength].decode("ascii", "replace")
        Cursor += ClassLength
        ClassId = struct.unpack_from("<H", DataValue, Cursor)[0]
        Cursor += 2
        if Count < 12:
            print(
                f"{Count:3d} {FieldName!r} id={FieldId} tag={Tag} "
                f"schema={Schema!r}/{SchemaId} class={ClassName!r}/{ClassId}"
            )
        Count += 1
    print("records", Count, "end", hex(Cursor))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
