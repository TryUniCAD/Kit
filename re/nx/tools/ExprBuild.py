from __future__ import annotations

import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).parent))

from AuthorName import SplicePayload
from ExprSchema import KClasses, KRefs
from MiddleBuild import EmitOne
from OmSection import BuildSection, ParseSection, Section

from convert.adapters.nx.PayloadReader import ReadPayload
from convert.adapters.nx.SplmReader import ReadSplm, RebuildSplm, SplmStreams

# the anchor identity is a saved pointer value; zero fails with 580143, all ones
# is accepted and means the slot is unset
KAnchorIdentity = b"\xff" * 7
KSectionIndex = 2


def Declarations() -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    References = [(Name, bytes.fromhex(Tail)) for Name, Tail in KRefs]
    Classes = [
        (
            Name,
            bytes.fromhex(Storage)
            + bytes.fromhex(Base)
            + bytes.fromhex(Fingerprint)
            + bytes.fromhex(Reference),
        )
        for Name, Storage, Base, Fingerprint, Reference in KClasses
    ]
    return References, Classes


def LaneLength(Items: list[tuple[str, bytes]]) -> int:
    return sum(1 + len(Name.encode("ascii")) + len(Tail) for Name, Tail in Items)


def HeaderLength(
    Name: bytes, References: list[tuple[str, bytes]], Classes: list[tuple[str, bytes]]
) -> int:
    return (
        0x29
        + len(Name)
        + 32
        + 4
        + 1
        + LaneLength(References)
        + 1
        + LaneLength(Classes)
    )


def EmitSection(
    Template: Section, Name: bytes, Value: float, Classes: list, References: list
) -> bytes:
    Header = HeaderLength(Template.part_name, References, Classes)
    Middle = EmitOne(Header, Name, Value, KAnchorIdentity)
    Counts = (7, 1, 0, len(Classes), 0, 0, 0, 0)
    ValueOut = Section(
        Template.version,
        Template.kind,
        Template.flags,
        Template.stamp,
        Template.part_name,
        Counts,
        Header + len(Middle),
        len(References) + 1,
        References,
        Classes,
        Middle,
        b"",
        bytes(12),
    )
    Body = BuildSection(ValueOut)
    Check = ParseSection(Body)
    if Check.middle != Middle:
        raise AssertionError("expression middle did not survive the section round trip")
    if len(Check.classes) != len(Classes) or len(Check.refs) != len(References):
        raise AssertionError("expression lanes did not survive the section round trip")
    return Body


def FirstExpression(Source: bytes, Name: bytes, Value: float) -> bytes:
    Parsed = ReadSplm(Source)
    Streams = dict(SplmStreams(Parsed))
    Payload = Streams["/Root/UG_PART/UG_PART"]
    Info = ReadPayload(Payload).sections
    Sections = [
        ParseSection(Payload[Entry.body_offset : Entry.body_offset + Entry.size])
        for Entry in Info
    ]
    References, Classes = Declarations()
    Body = EmitSection(Sections[KSectionIndex], Name, Value, Classes, References)
    Bodies = [
        Body if Index == KSectionIndex else BuildSection(Item)
        for Index, Item in enumerate(Sections)
    ]
    return RebuildSplm(Parsed, {"/Root/UG_PART/UG_PART": SplicePayload(Payload, Bodies)})


def Main(ArgValues: list[str]) -> int:
    if len(ArgValues) != 4:
        print("usage: ExprBuild.py <source.prt> <name> <value> <target.prt>")
        return 2
    Data = FirstExpression(
        FilePath(ArgValues[0]).read_bytes(), ArgValues[1].encode("ascii"), float(ArgValues[2])
    )
    FilePath(ArgValues[3]).write_bytes(Data)
    print("wrote", ArgValues[3], len(Data))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main(sys.argv[1:]))
