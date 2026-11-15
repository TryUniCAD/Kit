"""Research probe: which record's mask content is load bearing.

The mask lane accepts any values, but a section whose four lanes are all clean is rejected while a
single clean lane is accepted, so the content is validated per record. This builds one candidate per
record: the control payload with exactly that record's lane replaced by an all-clean vector.

The all-clean lane is emitted as `f6` plus `e7 7f` and `e7 7c`, so every repeat count fits in one byte
and the stream means the same thing whether a reader takes `e7` as a byte count or a compact count.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo.Header import ReadHeader
from convert.adapters.creo.Stream import StreamParser

KSlots = 252
Source = Path("re/creo/oracle/empty/solid_start_part_mmks.prt").read_bytes()
Header = ReadHeader(Source)

Payload = b""
for Table in Subset.ReadTables(Source, Header.base):
    for Entry in Table.rows:
        if Entry.name == "AllFeatur":
            Body = Source[Header.base + Entry.offset : Header.base + Entry.offset + Entry.length]
            Payload = Body[Body.find(b"\n") + 1 :]

Parser = StreamParser(Payload)
Spans: list[tuple[int, int, bool]] = []
Original = Parser.ReadField


def ReadField(Descriptor) -> object:
    Start = Parser.Reader.Position
    Node = Original(Descriptor)
    if Descriptor.name == "cr_flags_xar":
        Spans.append((Start, Parser.Reader.Position, Payload[Start] == 0xF1))
    return Node


Parser.ReadField = ReadField
Parser.Run()


def CleanElements() -> bytes:
    return b"\xF6" + b"\xE7\x7F" + b"\xE7\x7C"


def CleanLane(Defined: bool) -> bytes:
    return (b"\xF1\xF8\x80\xFC" if Defined else b"") + CleanElements()


for IndexText in sys.argv[1:]:
    IndexValue = int(IndexText)
    Start, End, Defined = Spans[IndexValue]
    Out = Payload[:Start] + CleanLane(Defined) + Payload[End:]
    Bodies = Author.EmptyPartSections((923, 979, 917))
    Bodies["AllFeatur"] = Author.SectionValue("AllFeatur", Out)
    Name = f"maskrec{IndexValue + 1}"
    Target = Path.home() / "Documents/creo-authored" / f"{Name}.prt"
    Target.write_bytes(Subset.Build(Source, Header.base, set(), Bodies))
    print(
        f"{Name}: record {IndexValue + 1} lane {End - Start} -> {len(CleanLane(Defined))} bytes"
        f", defined form {Defined}, AllFeatur {len(Payload)} -> {len(Out)}"
    )
