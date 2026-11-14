from __future__ import annotations
import re
import struct
import sys

from OmSection import ParseSection

KFeatureFlags = bytes.fromhex("0202020101010101")
KSystem = b"\x08SYSTEM\x00"
KAnchor = b"\x41"
KStatePattern = re.compile(rb"\x05(.)\x00\x00\1\1")


def BuildFeatureMiddle(
    HeaderLength: int,
    Product: bytes,
    State: bytes,
    Flags: bytes = KFeatureFlags,
) -> bytes:
    Buffer = bytearray()
    Buffer.extend(Flags)
    TextField = len(Buffer)
    Buffer.extend(bytes(4))
    Buffer.extend(bytes(0x2C - len(Buffer)))
    FirstField = len(Buffer)
    Buffer.extend(bytes(4))
    SecondField = len(Buffer)
    Buffer.extend(bytes(4))
    Buffer.extend(struct.pack("<III", 2, 1, 3))
    TextAt = len(Buffer)
    Buffer.extend(b"\x03\x01" + bytes([len(Product) + 2]) + Product + b"\x00")
    Buffer.extend(KSystem)
    AnchorAt = len(Buffer)
    Buffer.extend(KAnchor)
    StateAt = len(Buffer)
    Buffer.extend(State)
    Match = KStatePattern.search(Buffer, StateAt)
    if Match is None:
        raise ValueError("feature state lane has no class token landmark")
    struct.pack_into("<I", Buffer, TextField, HeaderLength + TextAt)
    struct.pack_into("<I", Buffer, FirstField, HeaderLength + AnchorAt)
    struct.pack_into("<I", Buffer, SecondField, HeaderLength + Match.start() + 4)
    return bytes(Buffer)


def Main(ArgValues: list[str]) -> int:
    from pathlib import Path

    from convert.adapters.nx.PayloadReader import ReadPayload
    from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

    for Name in ArgValues:
        Data = Path(Name).read_bytes()
        Streams = dict(SplmStreams(ReadSplm(Data)))
        Payload = Streams["/Root/UG_PART/UG_PART"]
        for Index, Info in enumerate(ReadPayload(Payload).sections):
            Body = Payload[Info.body_offset : Info.body_offset + Info.size]
            Section = ParseSection(Body)
            Position = Section.middle.find(b"\x03\x01")
            if Position < 0:
                continue
            Length = Section.middle[Position + 2]
            Product = Section.middle[Position + 3 : Position + 3 + (Length - 2)]
            if not Product.startswith(b"NX 25"):
                continue
            Header = len(Body) - len(Section.middle) - len(Section.record_area) - 12
            State = Section.middle[Section.middle.find(KSystem) + len(KSystem) + 1 :]
            if KStatePattern.search(State) is None:
                continue
            Rebuilt = BuildFeatureMiddle(
                Header, Product, State, Section.middle[:8]
            )
            print(
                Path(Name).name,
                "section",
                Index,
                "roundtrip",
                Rebuilt == Section.middle,
                len(Rebuilt),
                len(Section.middle),
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
