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


def Text(DataValue: bytes, Cursor: int, Length: int, End: int) -> str | None:
    if Length < 2 or Length > 200 or Cursor + Length > End:
        return None
    Symbols = DataValue[Cursor : Cursor + Length]
    if Symbols[-1] != 0:
        return None
    Body = Symbols[:-1]
    if not all(0x20 <= Byte < 0x7F for Byte in Body):
        return None
    return Body.decode("ascii")


def Body(DataValue: bytes, Cursor: int, End: int) -> tuple[dict, int] | None:
    if Cursor + 7 > End:
        return None
    FieldId = struct.unpack_from("<I", DataValue, Cursor)[0]
    if FieldId > 0x10000:
        return None
    if DataValue[Cursor + 4] != 7:
        return None
    SchemaLength = struct.unpack_from("<H", DataValue, Cursor + 5)[0]
    Schema = Text(DataValue, Cursor + 7, SchemaLength, End)
    if Schema is None:
        return None
    Cursor = Cursor + 7 + SchemaLength
    if Cursor + 6 > End:
        return None
    SchemaId = struct.unpack_from("<I", DataValue, Cursor)[0]
    if SchemaId > 0x10000:
        return None
    ClassLength = struct.unpack_from("<H", DataValue, Cursor + 4)[0]
    Class = Text(DataValue, Cursor + 6, ClassLength, End)
    if Class is None:
        return None
    Cursor = Cursor + 6 + ClassLength
    return (
        {
            "id": FieldId,
            "schema": Schema,
            "schema_id": SchemaId,
            "class": Class,
        },
        Cursor,
    )


def Record(DataValue: bytes, Cursor: int, End: int, Bare: bool) -> tuple[dict, int] | None:
    if Bare:
        for Length in range(1, 97):
            if Cursor + Length + 7 > End:
                return None
            Name = DataValue[Cursor : Cursor + Length]
            if not all(0x20 <= Byte < 0x7F for Byte in Name):
                break
            Tail = Body(DataValue, Cursor + Length, End)
            if Tail is None:
                continue
            Fields, Next = Tail
            Fields["name"] = Name.decode("ascii")
            return (Fields, Next)
        return None
    if Cursor + 2 > End:
        return None
    Length = struct.unpack_from("<H", DataValue, Cursor)[0]
    if not 1 <= Length <= 96:
        return None
    Name = DataValue[Cursor + 2 : Cursor + 2 + Length]
    if not all(0x20 <= Byte < 0x7F for Byte in Name):
        return None
    Tail = Body(DataValue, Cursor + 2 + Length, End)
    if Tail is None:
        return None
    Fields, Next = Tail
    Fields["name"] = Name.decode("ascii")
    return (Fields, Next)


def Main(ArgValues: list[str]) -> int:
    DataValue = Payload(ArgValues[0])
    Records = LegacyTable(DataValue)
    Start = ClassTableEnd(DataValue, Records)
    Section = ReadSections(DataValue)[0]
    End = Section.Offset + Section.Length
    Cursor = Start
    Count = 0
    Failures = 0
    while Cursor < End:
        Frame = Record(DataValue, Cursor, End, Count == 0) if Count == 0 else Record(
            DataValue, Cursor, End, False
        )
        if Frame is None:
            Frame = Record(DataValue, Cursor, End, True)
        if Frame is None:
            Failures += 1
            if Failures <= 4:
                print("stop", hex(Cursor), "byte", hex(DataValue[Cursor]))
            break
        Fields, Next = Frame
        if Count < 3:
            print(
                f"{Count} {hex(Cursor)} {Fields['name']!r} id={Fields['id']} "
                f"schema={Fields['schema']!r}/{Fields['schema_id']} "
                f"class={Fields['class']!r}"
            )
        Count += 1
        Cursor = Next
    print("file", Path(ArgValues[0]).name)
    print("start", hex(Start), "end", hex(End), "cursor", hex(Cursor))
    print("records", Count, "remaining", End - Cursor, "failures", Failures)
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
