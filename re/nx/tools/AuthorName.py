from __future__ import annotations
import re as RegexLib
import struct as StructLib
import sys
import uuid as UuidLib
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))
from OmSection import BuildSection, ParseSection, Section

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmBuild import BuildSplm
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

KPartSuffix = b".prt"
KNamePrefix = b"\x09\x00empty.prt"
KUuidPattern = RegexLib.compile(
    rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)

OffsetLane: dict[int, tuple[int | tuple[str, int], ...]] = {}
FrameLane: dict[int, int] = {}
PointerFactor: dict[int, int] = {}


def LearnLane(Source: list[Section], Target: list[Section], Delta: int) -> None:
    for Index, (Left, Right) in enumerate(zip(Source, Target)):
        First = Left.middle
        Second = bytearray(Right.middle)
        Frame = Second.find(bytes(Right.part_name))
        if Frame >= 0:
            FrameLane[Index] = Frame
            del Second[Frame + len(Left.part_name) : Frame + len(Right.part_name)]
        SecondBytes = bytes(Second)
        Lane: list[int | tuple[str, int]] = []
        Covered: set[int] = set()
        for Width in (4, 3, 2):
            for Position in range(0, min(len(First), len(SecondBytes)) - Width + 1):
                if Position in Covered:
                    continue
                Before = int.from_bytes(First[Position : Position + Width], "little")
                After = int.from_bytes(
                    SecondBytes[Position : Position + Width], "little"
                )
                if After - Before == Delta:
                    Lane.append(Position)
                    Covered.update(range(Position, Position + Width))
                elif After - Before == 2 * Delta and Index == 0:
                    Lane.append(("frame", Position))
                    Covered.update(range(Position, Position + Width))
        OffsetLane[Index] = tuple(Lane)
        PointerFactor[Index] = 2 if Index == 0 else 1


def ApplyDelta(
    Middle: bytearray, Lane: tuple[int | tuple[str, int], ...], Delta: int
) -> None:
    for Item in Lane:
        if isinstance(Item, tuple):
            Position = Item[1]
            StepValue = 2 * Delta
        else:
            Position = Item
            StepValue = Delta
        if Position + 4 > len(Middle):
            continue
        Value = StructLib.unpack_from("<I", Middle, Position)[0]
        StructLib.pack_into("<I", Middle, Position, Value + StepValue)


def BuildSections(Sections: list[Section], Name: bytes) -> list[bytes]:
    Delta = len(Name) - len(Sections[0].part_name)
    Bodies = []
    for Index, Item in enumerate(Sections):
        Middle = bytearray(Item.middle)
        Frame = FrameLane.get(Index)
        if Frame is not None:
            Start = Frame + 1
            Middle[Frame] = len(Name) + 2
            Middle[Start : Start + len(Item.part_name)] = Name
        ApplyDelta(Middle, OffsetLane[Index], Delta)
        Value = Section(
            Item.version,
            Item.kind,
            Item.flags,
            Item.stamp,
            Name,
            Item.counts,
            Item.pointer + Delta * PointerFactor[Index],
            Item.ref_count,
            list(Item.refs),
            list(Item.classes),
            bytes(Middle),
            Item.record_area,
            Item.digest,
        )
        Bodies.append(BuildSection(Value))
    return Bodies


def RebuildPayload(Payload: bytes, Bodies: list[bytes]) -> bytes:
    Parsed = ReadPayload(Payload)
    IndexEnd = Parsed.rows[1].value
    Remap: dict[int, int] = {}
    Cursor = IndexEnd
    Encoded = []
    for Index, (Info, Body) in enumerate(zip(Parsed.sections, Bodies)):
        Size = len(Body)
        Suffix = b"\xc0\xd1\xf1\xed" + (
            b"\xff\xff" if Index == len(Bodies) - 1 else b""
        )
        Remap[Info.offset] = Cursor
        Remap[Info.offset + Info.size] = Cursor + 12 + Size
        Encoded.append(
            b"\xff\xff\xff\xff" + bytes(4) + Size.to_bytes(4, "big") + Body + Suffix
        )
        Cursor += 12 + Size + len(Suffix)
    Remap[len(Payload)] = Cursor
    Remap[len(Payload) - 1] = Cursor - 1
    Remap[len(Payload) - 2] = Cursor - 2
    Rows = b"".join(
        StructLib.pack(
            "<III",
            *(
                Remap.get(Field, Field)
                for Field in (Row.type_code, Row.subtype_code, Row.value)
            ),
        )
        for Row in Parsed.rows
    )
    return Rows.ljust(IndexEnd, b"\x00") + b"".join(Encoded)


def RenameExternal(Data: bytes, Name: bytes) -> bytes:
    Old = KNamePrefix
    return Data.replace(Old, len(Name).to_bytes(1, "little") + b"\x00" + Name)


def WriteEmptyPart(
    Target: FilePath,
    Source: FilePath,
    Partner: FilePath,
    Name: bytes,
    DocumentId: bytes | None = None,
) -> bytes:
    SourceBytes = Source.read_bytes()
    Parsed = ReadSplm(SourceBytes)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Sections = [
        ParseSection(Payload[Item.body_offset : Item.body_offset + Item.size])
        for Item in ReadPayload(Payload).sections
    ]
    PartnerBytes = Partner.read_bytes()
    PartnerStreams = dict(SplmStreams(ReadSplm(PartnerBytes)))
    PartnerPayload = PartnerStreams["/Root/UG_PART/UG_PART"]
    PartnerSections = [
        ParseSection(PartnerPayload[Item.body_offset : Item.body_offset + Item.size])
        for Item in ReadPayload(PartnerPayload).sections
    ]
    LearnLane(Sections, PartnerSections, len(PartnerSections[0].part_name) - len(Sections[0].part_name))
    Bodies = BuildSections(Sections, Name)
    NewPayload = RebuildPayload(Payload, Bodies)
    External = RenameExternal(Streams["/Root/UG_PART/ExternalReferences"], Name)
    Trailer = bytearray(Parsed.header_trailer)
    Match = KUuidPattern.search(bytes(Trailer))
    Identity = DocumentId or str(UuidLib.uuid4()).encode("ascii")
    if Match is not None:
        Trailer[Match.start() : Match.start() + 36] = Identity
    Header = [
        ("/Root/", None),
        ("/Root/FastLoad/", None),
        ("/Root/part/", None),
        ("/Root/UG_PART/", None),
        ("/Root/FastLoad/RMFastLoad", b"\x00"),
        ("/Root/FastLoad/Structure", b"\x00"),
        ("/Root/FastLoad/ExternalReferences", b"\x00"),
        ("/Root/qafmetadata", b"\x00"),
        ("/Root/part/attrs", b"\x00"),
        ("/Root/UG_PART/ExternalReferences", External),
        ("/Root/UG_PART/UG_PART", NewPayload),
    ]
    DataValue = BuildSplm(
        Header,
        [("/Root/UG_PART/LastSavedToggleInfoStream", b"\x00")],
        FileTag=0x2BBA,
        HeaderTrailer=bytes(Trailer),
    )
    Target.write_bytes(DataValue)
    return DataValue


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 4:
        print("usage: AuthorName.py <source.prt> <partner.prt> <name.prt> <target.prt>")
        return 2
    DataValue = WriteEmptyPart(
        FilePath(ArgValues[3]), FilePath(ArgValues[0]), FilePath(ArgValues[1]), ArgValues[2].encode()
    )
    print("wrote", ArgValues[3], len(DataValue))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))


def SplicePayload(Payload: bytes, Bodies: list[bytes]) -> bytes:
    Parsed = ReadPayload(Payload)
    Remap: dict[int, int] = {}
    Output = bytearray()
    Cursor = 0
    for Index, (Info, Body) in enumerate(zip(Parsed.sections, Bodies)):
        Output.extend(Payload[Cursor : Info.offset])
        RegionEnd = (
            Parsed.sections[Index + 1].offset
            if Index + 1 < len(Parsed.sections)
            else len(Payload)
        )
        Keep = Payload[Info.offset + 12 + Info.size : RegionEnd]
        Start = len(Output)
        Output.extend(
            b"\xff\xff\xff\xff" + bytes(4) + len(Body).to_bytes(4, "big") + Body
        )
        Remap[Info.offset] = Start
        Remap[Info.offset + 12] = Start + 12
        Remap[Info.offset + 12 + Info.size] = Start + 12 + len(Body)
        Remap[Info.offset + 12 + Info.size + 4] = Start + 12 + len(Body) + 4
        Output.extend(Keep)
        Cursor = RegionEnd
    Output.extend(Payload[Cursor:])
    Remap[len(Payload)] = len(Output)
    Remap[len(Payload) - 1] = len(Output) - 1
    Remap[len(Payload) - 2] = len(Output) - 2
    Rows = bytearray(Payload[: Parsed.rows[1].value])
    for Offset in range(0, len(Rows) // 12 * 12, 12):
        for Field in range(3):
            Value = StructLib.unpack_from("<I", Rows, Offset + Field * 4)[0]
            if Value in Remap:
                StructLib.pack_into("<I", Rows, Offset + Field * 4, Remap[Value])
    return bytes(Rows) + bytes(Output)[len(Rows) :]
