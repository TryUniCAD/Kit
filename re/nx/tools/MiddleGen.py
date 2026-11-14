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




KTextMarker = b"\x03\x01"


def LanePositions(Lane) -> list[int]:
    return [Item[1] if isinstance(Item, tuple) else Item for Item in Lane]


def FindText(Middle: bytes) -> int:
    Position = Middle.find(KTextMarker)
    while Position >= 0:
        Length = Middle[Position + 2]
        Text = Middle[Position + 3 : Position + 3 + (Length - 2)]
        if Text.startswith(b"NX 25"):
            return Position
        Position = Middle.find(KTextMarker, Position + 1)
    raise ValueError("middle has no product text record")


def BuildMiddle(
    HeaderLength: int, Middle: bytes, Product: bytes, Lane
) -> bytes:
    TextAt = FindText(Middle)
    Length = Middle[TextAt + 2]
    OldText = Middle[TextAt + 3 : TextAt + 3 + (Length - 2)]
    Delta = len(Product) - len(OldText)
    TextEnd = TextAt + 3 + len(OldText) + 1
    Buffer = bytearray(Middle[:TextAt])
    Buffer.extend(KTextMarker + bytes([len(Product) + 2]) + Product + b"\x00")
    Buffer.extend(Middle[TextEnd:])
    for Position in LanePositions(Lane):
        if Position + 4 > len(Buffer):
            continue
        Value = struct.unpack_from("<I", Buffer, Position)[0]
        if Value - HeaderLength >= TextEnd:
            struct.pack_into("<I", Buffer, Position, Value + Delta)
    return bytes(Buffer)


def Check(Name: str, Product: bytes | None = None) -> None:
    from pathlib import Path as FilePath

    from convert.adapters.nx.PayloadReader import ReadPayload
    from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

    from AuthorName import LearnLane, OffsetLane

    Base = "/Users/odin/Documents/UniCAD/Kit/re/nx/oracle/"
    Empty = FilePath(Base + "empty.prt").read_bytes()
    Partner = FilePath(Base + "empty_alpha.prt").read_bytes()

    def Sections(Data: bytes):
        Streams = dict(SplmStreams(ReadSplm(Data)))
        Payload = Streams["/Root/UG_PART/UG_PART"]
        return [
            ParseSection(Payload[Item.body_offset : Item.body_offset + Item.size])
            for Item in ReadPayload(Payload).sections
        ], Payload

    Left, _ = Sections(Empty)
    Right, _ = Sections(Partner)
    LearnLane(Left, Right, len(Right[0].part_name) - len(Left[0].part_name))
    Target, Payload = Sections(FilePath(Base + Name).read_bytes())
    Info = ReadPayload(Payload).sections
    for Index, Section in enumerate(Target):
        Body = Payload[Info[Index].body_offset : Info[Index].body_offset + Info[Index].size]
        Header = len(Body) - len(Section.middle) - len(Section.record_area) - 12
        try:
            Rebuilt = BuildMiddle(
                Header,
                Section.middle,
                Product or b"NX 2506.9120 - External User Function",
                OffsetLane.get(Index, ()),
            )
        except ValueError:
            continue
        print(Name, "section", Index, "roundtrip", Rebuilt == Section.middle, len(Rebuilt), len(Section.middle))


if __name__ == "__main__":
    for Value in sys.argv[1:]:
        Check(Value)
