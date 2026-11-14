from __future__ import annotations

import struct as Struct
import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from OmSection import BuildSection, ParseSection, Section

from convert.adapters.nx.PayloadBuild import ResizePayload
from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams

KVersion = b"NX 2506.9120 - External User Function"
KNames = b"\x02\x18m_legacyInactiveModules\x81\x0c"
KCounter = 0x3D8
KZeros = 64
KObjects = 3
KHead = b"\x41\x00\x03\x05\x01\x00\x04\x05\x02\x00"
KAnchor = b"\xe0\x6a\xf8"
KUnset = b"\xff" * 7
KOrder = (3, 1, 3, 4)
KHeadTail = bytes.fromhex("05021306020000")
# the body less middle is a fixed preamble followed by three objects
def EmptyMiddle(
    Base: int,
    Descriptor: bytes,
    Record: bytes,
    Identity: bytes = KUnset,
    Counter: int = KCounter,
) -> bytes:
    Flags = bytes([2]) * 8 + bytes([1]) * 9
    Anchor = (
        b"\x03\x01"
        + bytes([len(KVersion) + 2])
        + KVersion
        + b"\x00"
        + b"\x08SYSTEM\x00"
    )
    Head = KHead + KAnchor + Identity + KHeadTail
    Order = b"".join(Value.to_bytes(4, "little") for Value in KOrder)
    Preamble = KNames + Flags + Counter.to_bytes(4, "little") + bytes(KZeros)
    First = len(Preamble) + 4 * KObjects + len(Order) + len(Anchor)
    Offsets = [First, First + len(Head), First + len(Head) + len(Descriptor)]
    Table = b"".join((Base + Offset).to_bytes(4, "little") for Offset in Offsets)
    return b"".join((Preamble, Table, Order, Anchor, Head, Descriptor, Record))


# adopting keeps the class lanes and replaces the middle and pointer
def Adopt(Template: Section, Middle: bytes) -> bytes:
    def Build(Pointer: int) -> bytes:
        return BuildSection(
            Section(
                Template.version,
                Template.kind,
                Template.flags,
                Template.stamp,
                Template.part_name,
                Template.counts,
                Pointer,
                Template.ref_count,
                list(Template.refs),
                list(Template.classes),
                Middle,
                Template.record_area,
                Template.digest,
            )
        )

    return Build(len(Build(0)) - 12)


def Load(Name: str) -> tuple[bytes, bytes, list[bytes], list[Section]]:
    Data = FilePath(Name).read_bytes()
    Parsed = ReadSplm(Data)
    Payload = dict(SplmStreams(Parsed))["/Root/UG_PART/UG_PART"]
    Info = ReadPayload(Payload)
    Bodies = [
        Payload[Entry.body_offset : Entry.body_offset + Entry.size]
        for Entry in Info.sections
    ]
    return (Payload, Parsed, Bodies, [ParseSection(Body) for Body in Bodies])


def Main(ArgValues: list[str]) -> int:
    Base = "/Users/odin/Documents/UniCAD/Kit/re/nx/oracle/"
    for Name in ("empty.prt", "multi.prt"):
        _, _, _, Sections = Load(Base + Name)
        Middle = Sections[1].middle
        Base_ = Sections[1].pointer - len(Middle)
        Built = EmptyMiddle(
            Base_,
            Sections[1].middle[0xD8:0xF4],
            Sections[1].middle[0xF4:],
            Sections[1].middle[0xCA:0xD1],
        )
        print(
            Name,
            "base",
            hex(Base_),
            "len",
            len(Built),
            "identical",
            Built == Middle,
        )
    Payload, Parsed, Bodies, Sections = Load(Base + ArgValues[0])
    Middle = EmptyMiddle(
        Sections[1].pointer - len(Sections[1].middle),
        Sections[1].middle[0xD8:0xF4],
        Sections[1].middle[0xF4:],
        Sections[1].middle[0xCA:0xD1],
    )
    Bodies = list(Bodies)
    Bodies[1] = Adopt(Sections[1], Middle)
    Written = ResizePayload(Payload, Bodies)
    Last = ReadPayload(Written).sections[-1]
    Written = Written[: Last.body_offset + Last.size]
    FilePath(Base + ArgValues[1]).write_bytes(
        RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": Written})
    )
    print("wrote", ArgValues[1], len(Written))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
