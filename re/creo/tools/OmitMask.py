"""Research probe: delete the cr_flags_xar field from every AllFeatur record.

Record 0 declares the field as `e0 01 cr_flags_xar 00` followed by `f1 f8 80 fc` and the elements.
Records 1..3 replay positionally: only the element bytes, no header and no array count.

Two variants are produced because the leading `f1` in record 0 may belong either to the field or to
the close of the preceding field:

- A: header and `f8 80 fc` and elements removed, `f1` kept;
- B: header from `e0` through the elements removed, `f1` removed with it.
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

Source = Path("re/creo/oracle/empty/solid_start_part_mmks.prt").read_bytes()
Header = ReadHeader(Source)

Payload = b""
for Table in Subset.ReadTables(Source, Header.base):
    for Entry in Table.rows:
        if Entry.name == "AllFeatur":
            Body = Source[Header.base + Entry.offset : Header.base + Entry.offset + Entry.length]
            Payload = Body[Body.find(b"\n") + 1 :]

Parser = StreamParser(Payload)
Spans: list[tuple[int, int]] = []
Original = Parser.ReadField


def ReadField(Descriptor) -> object:
    Start = Parser.Reader.Position
    Node = Original(Descriptor)
    if Descriptor.name == "cr_flags_xar":
        Spans.append((Start, Parser.Reader.Position))
    return Node


Parser.ReadField = ReadField
Parser.Run()

HeaderStart = Payload.rfind(b"\xe0\x01cr_flags_xar\x00", 0, Spans[0][0])
assert HeaderStart >= 0
Declared = (HeaderStart, Spans[0][1])
Delivered = [(Start, End) for Start, End in Spans[1:]]
Keep1 = (Spans[0][0], Spans[0][1])
Drop1 = (Spans[0][0] + 1, Spans[0][1])
Count = Payload[Spans[0][0] + 1 : Spans[0][0] + 4]
assert Count == b"\xf8\x80\xfc", Count


def Remove(Data: bytes, Ranges: list[tuple[int, int]]) -> bytes:
    Out = Data
    for Start, End in sorted(Ranges, reverse=True):
        Out = Out[:Start] + Out[End:]
    return Out


Variants = {
    "omit_a": [(HeaderStart, Spans[0][1])] + Delivered,
    "omit_b": [(HeaderStart, Spans[0][1] - 0)] + Delivered,
}
for Name, Ranges in Variants.items():
    New = Remove(Payload, Ranges)
    Bodies = Author.EmptyPartSections((923, 979, 917))
    Bodies["AllFeatur"] = Author.SectionValue("AllFeatur", New)
    Target = Path.home() / "Documents/creo-authored" / f"{Name}.prt"
    Result = Subset.Build(Source, Header.base, set(), Bodies)
    Target.write_bytes(Result)
    print(f"{Name}: {len(Result)} bytes, allfeatur {len(Payload)} -> {len(New)}")
