from __future__ import annotations

import struct as Struct
import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from OmSection import ParseSection, Section

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

KTableStart = 0xCD
KHeadTag = b"\x02\x02"
KLongTail = b"\x93\x8a"
KShortTail = b"\x93\x8c"
KFlag = 0xF0
KCount = 0x09


def Execute(Name: str) -> tuple[bytes, Section]:
    Data = FilePath(Name).read_bytes()
    Parsed = ReadSplm(Data)
    Payload = dict(SplmStreams(Parsed))["/Root/UG_PART/UG_PART"]
    Info = ReadPayload(Payload).sections[1]
    Body = Payload[Info.body_offset : Info.body_offset + Info.size]
    return (Body, ParseSection(Body))


def Table(Middle: bytes, Body: bytes, Count: int) -> list[int]:
    for Start in range(0, len(Middle) - 4 * Count):
        Offsets: list[int] = []
        Position = Start
        while len(Offsets) < Count and Position + 4 <= len(Middle):
            Value = int(Struct.unpack_from("<I", Middle, Position)[0])
            if Offsets and Value <= Offsets[-1]:
                break
            if Value >= len(Body):
                break
            Offsets.append(Value)
            Position += 4
        if len(Offsets) != Count:
            continue
        Follow = Position + 4
        if Follow > len(Middle):
            continue
        Order = int(Struct.unpack_from("<I", Middle, Position)[0])
        if Order <= Count:
            return Offsets
    raise ValueError("construction section object table was not found")


def Descriptor(Record: bytes) -> dict[str, object]:
    Fields: dict[str, object] = {"bytes": len(Record)}
    if Record.startswith(KHeadTag):
        Fields["tag"] = "descriptor"
    elif Record[:1] == b"\x41":
        Fields["tag"] = "head"
    else:
        Fields["tag"] = "entry"
    Marker = Record.find(bytes([KFlag]))
    if Marker > 0 and Marker + 1 < len(Record):
        Fields["object"] = Record[Marker + 1]
    Weight = Record.find(bytes([KCount]), Marker + 1) if Marker > 0 else -1
    if Weight > 0 and Weight + 1 < len(Record):
        Fields["weight"] = Record[Weight + 1]
    if Record.endswith(KLongTail):
        Fields["tail"] = "long"
    elif Record.endswith(KShortTail):
        Fields["tail"] = "short"
    return Fields


def Sizes(Offsets: list[int], Body: bytes) -> list[int]:
    Ends = Offsets[1:] + [len(Body) - 12]
    return [End - Start for Start, End in zip(Offsets, Ends)]


def Report(Name: str) -> None:
    Body, Section = Execute(Name)
    Offsets = Table(Section.middle, Body, Section.counts[0])
    Lengths = Sizes(Offsets, Body)
    print(
        Name,
        "counts",
        Section.counts,
        "classes",
        len(Section.classes),
        "refs",
        len(Section.refs),
        "objects",
        len(Offsets),
    )
    Order = Section.middle[KTableStart + 4 * len(Offsets) :]
    Indices = [
        int(Struct.unpack_from("<I", Order, Position)[0])
        for Position in range(0, 4 * len(Offsets), 4)
    ]
    print("  order", Indices[:12], "..." if len(Indices) > 12 else "")
    for Index, (Offset, Length) in enumerate(zip(Offsets, Lengths)):
        Fields = Descriptor(Body[Offset : Offset + Length])
        print(
            f"  {Index:2d} off {Offset:5d} len {Length:3d} "
            f"{Fields.get('tag','?'):10s} object {Fields.get('object','?')} "
            f"weight {Fields.get('weight','?')} tail {Fields.get('tail','-')}"
        )


def Main(ArgValues: list[str]) -> int:
    for Name in ArgValues:
        Report(Name)
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
