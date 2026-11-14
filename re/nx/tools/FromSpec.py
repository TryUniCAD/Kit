from __future__ import annotations
import struct
import sys
from pathlib import Path

sys.path.insert(0, "re/nx/tools")
from OmSection import BuildSection, Section
from SchemaEmpty import KExternalReferences, KFiller, KRows, KSections, KTrailer

from convert.adapters.nx.SplmBuild import BuildSplm

KProduct = b"NX 2506.9120 - External User Function"


def MakeSpecs() -> list[dict[str, object]]:
    return [
        {
            "version": Item["version"],
            "kind": Item["kind"],
            "flags": Item["flags"],
            "stamp": Item["stamp"],
            "part_name": Item["part_name"],
            "counts": tuple(Item["counts"]),
            "pointer": Item["pointer"],
            "ref_count": Item["ref_count"],
            "refs": [(Name, bytes.fromhex(Tail)) for Name, Tail in Item["refs"]],
            "classes": [
                (Name, bytes.fromhex(Tail)) for Name, Tail in Item["classes"]
            ],
            "middle": bytes.fromhex(Item["middle"]),
            "record": bytes.fromhex(Item["record"]),
            "digest": bytes.fromhex(Item["digest"]),
        }
        for Item in KSections
    ]


def BuildPayload(
    Specs: list[dict[str, object]],
    Product: bytes,
    PartName: bytes | None = None,
) -> bytes:
    if len(Product) != len(KProduct):
        raise ValueError("product text length must stay constant")
    OldName = bytes(Specs[0]["part_name"])
    if PartName is not None and len(PartName) != len(OldName):
        raise ValueError("part name length must stay constant")
    IndexEnd = KRows[1][2]
    Bodies = []
    for Item in Specs:
        Middle = bytes(Item["middle"]).replace(KProduct, Product)
        if PartName is not None:
            Middle = Middle.replace(OldName, PartName)
        Value = Section(
            int(Item["version"]),
            int(Item["kind"]),
            int(Item["flags"]),
            int(Item["stamp"]),
            PartName if PartName is not None else bytes(Item["part_name"]),
            tuple(Item["counts"]),
            int(Item["pointer"]),
            int(Item["ref_count"]),
            list(Item["refs"]),
            list(Item["classes"]),
            Middle,
            bytes(Item["record"]).replace(OldName, PartName) if PartName is not None else bytes(Item["record"]),
            bytes(Item["digest"]),
        )
        Bodies.append(BuildSection(Value))
    OldOffsets: dict[int, int] = {}
    NewOffsets: dict[int, int] = {}
    OldCursor = IndexEnd
    NewCursor = IndexEnd
    for Index, (Item, Body) in enumerate(zip(Specs, Bodies)):
        Suffix = 4 + (2 if Index == len(Bodies) - 1 else 0)
        OldSize = len(BuildSection(Section(
            int(Item["version"]),
            int(Item["kind"]),
            int(Item["flags"]),
            int(Item["stamp"]),
            PartName if PartName is not None else bytes(Item["part_name"]),
            tuple(Item["counts"]),
            int(Item["pointer"]),
            int(Item["ref_count"]),
            list(Item["refs"]),
            list(Item["classes"]),
            bytes(Item["middle"]),
            bytes(Item["record"]).replace(OldName, PartName) if PartName is not None else bytes(Item["record"]),
            bytes(Item["digest"]),
        )))
        OldOffsets[OldCursor] = NewCursor
        OldOffsets[OldCursor + 12 + OldSize] = NewCursor + 12 + len(Body)
        OldCursor += 12 + OldSize + Suffix
        NewCursor += 12 + len(Body) + Suffix
    Rows = b"".join(
        struct.pack("<III", Row[0], Row[1], OldOffsets.get(Row[2], Row[2]))
        for Row in KRows
    )
    Encoded = []
    for Index, Body in enumerate(Bodies):
        Suffix = b"\xc0\xd1\xf1\xed" + (
            b"\xff\xff" if Index == len(Bodies) - 1 else b""
        )
        Encoded.append(
            b"\xff\xff\xff\xff"
            + bytes(4)
            + len(Body).to_bytes(4, "big")
            + Body
            + Suffix
        )
    return Rows + bytes.fromhex(KFiller) + b"".join(Encoded)


def WritePart(
    Target: Path, Product: bytes, PartName: bytes | None = None
) -> None:
    Payload = BuildPayload(MakeSpecs(), Product, PartName)
    External = bytes.fromhex(KExternalReferences)
    if PartName is not None:
        External = External.replace(b"empty.prt", PartName)
    Header = [
        ("/Root/", None),
        ("/Root/FastLoad/", None),
        ("/Root/part/", None),
        ("/Root/UG_PART/", None),
        ("/Root/FastLoad/RMFastLoad", b"\0"),
        ("/Root/FastLoad/Structure", b"\0"),
        ("/Root/FastLoad/ExternalReferences", b"\0"),
        ("/Root/qafmetadata", b"\0"),
        ("/Root/part/attrs", b"\0"),
        ("/Root/UG_PART/ExternalReferences", External),
        ("/Root/UG_PART/UG_PART", Payload),
    ]
    Data = BuildSplm(
        Header,
        [("/Root/UG_PART/LastSavedToggleInfoStream", b"\0")],
        FileTag=0x2BBA,
        HeaderTrailer=bytes.fromhex(KTrailer),
    )
    Target.write_bytes(Data)
    print("wrote", Target, len(Data))


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 1:
        print("usage: FromSpec.py <target.prt>")
        return 2
    WritePart(Path(ArgValues[0]), KProduct)
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
