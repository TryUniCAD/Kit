from __future__ import annotations

import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from OmSection import BuildSection, ParseSection, Section

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.PayloadBuild import ResizePayload
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams

KVersion = b"NX 2506.9120 - External User Function"
KAnchor = b"\xe0\x6a\xf8"
KUnset = b"\xff" * 7
KStub = b"OM\x01\x01"
KTail = bytes.fromhex(
    "04021305020000"
    "0202ffff00ffff000000"
    "ffffffff0000ff00ffff"
    "ffffff0000ff00ffff00"
    "ffff00ff0101"
)
KCounterGap = 49
KCounterTail = 76


def RootMiddle(Counter: int, Identity: bytes) -> bytes:
    if len(Identity) != 7:
        raise ValueError("nx anchor identity is seven bytes")
    return b"".join(
        (
            bytes([2, 2, 2, 1, 1, 1, 1, 1]),
            Counter.to_bytes(4, "little"),
            bytes(0x20),
            (Counter + KCounterGap).to_bytes(4, "little"),
            (Counter + KCounterTail).to_bytes(4, "little"),
            (2).to_bytes(4, "little"),
            (1).to_bytes(4, "little"),
            (3).to_bytes(4, "little"),
            b"\x03\x01" + bytes([len(KVersion) + 2]),
            KVersion,
            b"\x00",
            b"\x08SYSTEM\x00",
            b"\x41\x00",
            b"\x03\x05\x01\x00",
            b"\x04\x05\x02\x00",
            KAnchor,
            Identity,
            KTail,
        )
    )


def Load(Name: str) -> tuple[bytes, bytes, list[bytes], list[Section]]:
    Data = FilePath(Name).read_bytes()
    Parsed = ReadSplm(Data)
    Payload = dict(SplmStreams(Parsed))["/Root/UG_PART/UG_PART"]
    Info = ReadPayload(Payload)
    Bodies = [
        Payload[Entry.body_offset : Entry.body_offset + Entry.size]
        for Entry in Info.sections
    ]
    Sections = [ParseSection(Body) for Body in Bodies]
    return (Payload, Parsed, Bodies, Sections)


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

    probe = Build(0)
    return Build(len(probe) - 12)


def Main(ArgValues: list[str]) -> int:
    Base = "/Users/odin/Documents/UniCAD/Kit/re/nx/oracle/"
    Fixtures = (
        "dim40.prt",
        "const_box60.prt",
        "empty.prt",
        "empty_expr.prt",
        "multi.prt",
        "sweep.prt",
    )
    for Name in Fixtures:
        _, _, _, Sections = Load(Base + Name)
        Middle = Sections[3].middle
        Counter = int.from_bytes(Middle[0x08:0x0C], "little")
        Built = RootMiddle(Counter, Middle[0x7E:0x85])
        print(
            Name,
            "counter",
            hex(Counter),
            "len",
            len(Built),
            "identical",
            Built == Middle,
        )
    Payload, Parsed, Bodies, Sections = Load(Base + ArgValues[0])
    Middle = RootMiddle(0x1E3, KUnset)
    Bodies = list(Bodies)
    Bodies[3] = Adopt(Sections[3], Middle)
    Bodies[4] = KStub
    Written = ResizePayload(Payload, Bodies)
    Last = ReadPayload(Written).sections[-1]
    Written = Written[: Last.body_offset + Last.size]
    Target = Base + ArgValues[1]
    FilePath(Target).write_bytes(
        RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": Written})
    )
    print("wrote", Target, len(Written), "sections", len(ReadPayload(Written).sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
