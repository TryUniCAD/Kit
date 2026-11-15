"""Research probe: which cr_flags_xar slots are load critical.

The lane is now fully encodable (`Author.FlagValue`, `Author.SignedIntElements`), so a candidate can
replace whole slot ranges with the all-clean sentinel `-1` in every feature record and still be a
well formed stream. Bisecting the slot range that has to keep the control values locates the slots the
loader actually validates, which is the smallest thing that then has to be explained.
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
Spans: list[tuple[int, int, tuple[int, ...]]] = []
Original = Parser.ReadField


def ReadField(Descriptor) -> object:
    Start = Parser.Reader.Position
    Node = Original(Descriptor)
    if Descriptor.name == "cr_flags_xar":
        Spans.append((Start, Parser.Reader.Position, tuple(getattr(Node, "value", ()))))
    return Node


Parser.ReadField = ReadField
Parser.Run()


def Candidate(
    NameText: str,
    Low: int,
    High: int | None,
    Literal: int | None = None,
    Length: int | None = None,
) -> None:
    Out = Payload
    for IndexValue in range(len(Spans) - 1, -1, -1):
        Start, End, Values = Spans[IndexValue]
        if Length is not None:
            Kept = (-1,) * Length
        elif Literal is None:
            Kept = tuple(
                -1 if High is None or Low <= SlotIndex < High else Value
                for SlotIndex, Value in enumerate(Values)
            )
        else:
            Kept = tuple(
                Literal if SlotIndex == Low else Value
                for SlotIndex, Value in enumerate(Values)
            )
        Lane = (
            Author.FlagValue(Kept) if IndexValue == 0 else Author.SignedIntElements(Kept)
        )
        Out = Out[:Start] + Lane + Out[End:]
    Bodies = Author.EmptyPartSections((923, 979))
    Bodies["AllFeatur"] = Author.SectionValue("AllFeatur", Out)
    Target = Path.home() / "Documents/creo-authored" / f"{NameText}.prt"
    Target.write_bytes(Subset.Build(Source, Header.base, set(), Bodies))
    print(f"{NameText}: slots {Low}..{High} cleaned, AllFeatur {len(Payload)} -> {len(Out)}")


for Statement in sys.argv[1:]:
    NameText, BoundsText = Statement.split("=")
    if BoundsText == "all":
        Candidate(NameText, 0, None)
        continue
    if BoundsText.startswith("len:"):
        Candidate(NameText, 0, None, -1, int(BoundsText.split(":")[1]))
        continue
    if ":" in BoundsText:
        SlotText, ValueText = BoundsText.split(":")
        Candidate(NameText, int(SlotText), None, int(ValueText))
        continue
    LowText, HighText = BoundsText.split(",")
    Candidate(NameText, int(LowText), int(HighText))
