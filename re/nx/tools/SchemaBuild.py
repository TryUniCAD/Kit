from __future__ import annotations
import struct
import sys
import uuid as UuidLib
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))
from AuthorName import SplicePayload
from MiddleGen import BuildMiddle
from OmSection import ParseSection, Section
from SchemaTable import KClasses, KRefs

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmBuild import BuildSplm
from convert.adapters.nx.SplmReader import ReadSplm, SplmStreams

KProduct = b"NX 2506.9120 - External User Function"


def RefPairs(Index: int) -> list[tuple[str, bytes]]:
    return [(Name, bytes.fromhex(Code)) for Name, Code in KRefs[Index]]


def ClassPairs(Index: int) -> list[tuple[str, bytes]]:
    return [
        (Name, bytes.fromhex(Storage) + bytes.fromhex(Base) + bytes.fromhex(Fp) + bytes.fromhex(Ref))
        for Name, Storage, Base, Fp, Ref in KClasses[Index]
    ]


def BuildSections(
    Sections: list[Section], Payload: bytes, Product: bytes, Indices: set[int]
) -> list[bytes]:
    from OmSection import BuildSection

    Bodies = []
    Info = ReadPayload(Payload).sections
    for Index, Item in enumerate(Sections):
        Body = Payload[Info[Index].body_offset : Info[Index].body_offset + Info[Index].size]
        Header = len(Body) - len(Item.middle) - len(Item.record_area) - 12
        Middle = Item.middle
        if Index in Indices:
            try:
                Middle = BuildMiddle(Header, Item.middle, Product, ())
            except ValueError:
                Middle = Item.middle
        Delta = len(Middle) - len(Item.middle)
        Bodies.append(
            BuildSection(
                Section(
                    Item.version,
                    Item.kind,
                    Item.flags,
                    Item.stamp,
                    Item.part_name,
                    Item.counts,
                    Item.pointer + Delta,
                    Item.ref_count,
                    RefPairs(Index),
                    ClassPairs(Index),
                    Middle,
                    Item.record_area,
                    Item.digest,
                )
            )
        )
    return Bodies


def BuildEmpty(Source: FilePath, Target: FilePath) -> bytes:
    Data = Source.read_bytes()
    Parsed = ReadSplm(Data)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Sections = [
        ParseSection(Payload[Item.body_offset : Item.body_offset + Item.size])
        for Item in ReadPayload(Payload).sections
    ]
    Bodies = BuildSections(Sections, Payload, KProduct, {3})
    NewPayload = SplicePayload(Payload, Bodies)
    Trailer = bytearray(Parsed.header_trailer)
    Trailer[0x132:0x132 + 36] = str(UuidLib.uuid4()).encode("ascii")
    Header = [("/Root/", None), ("/Root/FastLoad/", None), ("/Root/part/", None), ("/Root/UG_PART/", None)]
    Header += [
        ("/Root/FastLoad/RMFastLoad", b"\x00"),
        ("/Root/FastLoad/Structure", b"\x00"),
        ("/Root/FastLoad/ExternalReferences", b"\x00"),
        ("/Root/qafmetadata", b"\x00"),
        ("/Root/part/attrs", b"\x00"),
        ("/Root/UG_PART/ExternalReferences", Streams["/Root/UG_PART/ExternalReferences"]),
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
    if len(ArgValues) != 2:
        print("usage: SchemaBuild.py <source.prt> <target.prt>")
        return 2
    Data = BuildEmpty(FilePath(ArgValues[0]), FilePath(ArgValues[1]))
    print("wrote", ArgValues[1], len(Data))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
