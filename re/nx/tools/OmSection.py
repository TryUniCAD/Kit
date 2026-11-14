from __future__ import annotations
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

KPlatform = b"x64/Windows NT"


@dataclass
class Section:
    header: bytes
    ref_count: int
    refs: list[tuple[str, bytes]]
    classes: list[tuple[str, bytes]]
    middle: bytes
    record_area: bytes
    digest: bytes = bytes(12)


def ReadToken(Data: bytes, At: int) -> tuple[int, int]:
    Prefix = Data[At]
    if Prefix <= 0x7F:
        return (Prefix, 1)
    if 0x80 <= Prefix <= 0x8F:
        return ((Prefix - 0x80) * 256 + Data[At + 1] + 1, 2)
    if Prefix == 0x90 or 0xA0 <= Prefix <= 0xAF or Prefix == 0xF1:
        Value = ((Prefix & 0x0F) << 16) | (Data[At + 1] << 8) | Data[At + 2]
        return (Value + 1, 3)
    raise ValueError("bad registry token")


def ReadDeclaration(Data: bytes, At: int) -> tuple[str, int, int]:
    Declared = Data[At]
    NameLength = Declared - 1
    if NameLength <= 0:
        raise ValueError("bad declaration length")
    Name = Data[At + 1 : At + 1 + NameLength]
    if not all(0x20 <= Item < 0x7F for Item in Name):
        raise ValueError("bad declaration name")
    return (Name.decode("ascii"), At + 1 + NameLength, At)


def ParseSection(Body: bytes) -> Section:
    if Body[:4] != b"OM\x01\x01":
        raise ValueError("not an om section")
    Header = Body[:0x56]
    Pointer = struct.unpack_from("<I", Header, 0x52)[0]
    RefCount = Body[0x56]
    Refs: list[tuple[str, bytes]] = []
    Classes: list[tuple[str, bytes]] = []
    Pos = 0x57
    while True:
        if Body[Pos] == 0x01:
            Pos += 1
            break
        Name, TailAt, _ = ReadDeclaration(Body, Pos)
        Refs.append((Name, Body[TailAt : TailAt + 1]))
        Pos = TailAt + 1
    while Body[Pos] != 0x02:
        try:
            Name, TailAt, _ = ReadDeclaration(Body, Pos)
            StorageWidth = ReadToken(Body, TailAt)[1]
            BaseWidth = ReadToken(Body, TailAt + StorageWidth)[1]
            TailEnd = TailAt + StorageWidth + BaseWidth + 8
            TailEnd += ReadToken(Body, TailEnd)[1]
        except (ValueError, IndexError):
            break
        Classes.append((Name, Body[TailAt:TailEnd]))
        Pos = TailEnd
    Middle = Body[Pos:Pointer]
    RecordArea = Body[Pointer : len(Body) - 12]
    Digest = Body[-12:]
    return Section(Header, RefCount, Refs, Classes, Middle, RecordArea, Digest)


def WriteDeclaration(Name: bytes, Tail: bytes) -> bytes:
    return bytes([len(Name) + 1]) + Name + Tail


def BuildSection(Value: Section) -> bytes:
    Body = bytearray(Value.header)
    Body.append(Value.ref_count)
    for Name, Tail in Value.refs:
        Body.extend(WriteDeclaration(Name.encode("ascii"), Tail))
    Body.append(0x01)
    for Name, Tail in Value.classes:
        Body.extend(WriteDeclaration(Name.encode("ascii"), Tail))
    Body.extend(Value.middle)
    Body.extend(Value.record_area)
    Body.extend(Value.digest)
    struct.pack_into("<I", Body, 0x52, len(Body) - 12)
    return bytes(Body)


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 1:
        print("usage: OmSection.py <part.prt>")
        return 2
    Data = Path(ArgValues[0]).read_bytes()
    Parsed = ReadSplm(Data)
    Streams = dict(SplmStreams(Parsed))
    PartData = Streams["/Root/UG_PART/UG_PART"]
    Payload = ReadPayload(PartData)
    for Index, SectionInfo in enumerate(Payload.sections):
        Body = PartData[SectionInfo.body_offset : SectionInfo.body_offset + SectionInfo.size]
        Value = ParseSection(Body)
        Rebuilt = BuildSection(Value)
        print(
            "section",
            Index,
            "size",
            len(Body),
            "refs",
            [Name for Name, _ in Value.refs],
            "classes",
            [Name for Name, _ in Value.classes][:6],
            "middle",
            len(Value.middle),
            "record_area",
            len(Value.record_area),
            "roundtrip",
            Rebuilt == Body,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
