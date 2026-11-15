"""Research probe: is the cr_flags_xar lane capped at 0x1a0 bytes?

The accessor family in `xtop.exe` uses `size(kind)` values of `0`, `0xd0` and `0x1a0`. The control's
lane value is 402 bytes; every earlier re-encode that Creo rejected was 459 or 485 bytes, and the one
that was accepted was 403. This probe builds lanes of the same 252 values at several sizes below and
above `0x1a0` by expanding repeat tokens, so the cap can be located by bisection.

Smaller is not always accepted: the all-`-1` and all-`0` lanes were 255 bytes and both failed, so a
pass here would separate "the value array is correct" from "these particular values are invalid".
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

KCAP = 0x1A0

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

Lane = Payload[Spans[0][0] : Spans[0][1]]
Intro = Lane[:4]
Elements = Lane[4:]
assert Intro == b"\xf1\xf8\x80\xfc", Intro


def Tokenize(Data: bytes) -> list[bytes]:
    Tokens: list[bytes] = []
    Index = 0
    while Index < len(Data):
        Byte = Data[Index]
        if Byte == 0xF6:
            Tokens.append(Data[Index : Index + 1])
            Index += 1
        elif Byte == 0xF5:
            Index += 1
            Mark = Data[Index]
            if Mark <= 0x7F:
                Size = 1
            elif Mark <= 0xBF:
                Size = 2
            elif Mark <= 0xDF:
                Size = 3
            else:
                Size = 1 + (Mark - 0xE7)
            Tokens.append(Data[Index - 1 : Index + Size])
            Index += Size
        elif 0xE4 <= Byte <= 0xE6:
            Tokens.append(Data[Index : Index + 1])
            Index += 1
        elif Byte == 0xE7:
            Tokens.append(Data[Index : Index + 2])
            Index += 2
        elif Byte <= 0x7F:
            Tokens.append(Data[Index : Index + 1])
            Index += 1
        elif Byte <= 0xBF:
            Tokens.append(Data[Index : Index + 2])
            Index += 2
        elif Byte <= 0xDF:
            Tokens.append(Data[Index : Index + 3])
            Index += 3
        elif 0xE8 <= Byte <= 0xEB:
            Size = 1 + (Byte - 0xE7)
            Tokens.append(Data[Index : Index + Size])
            Index += Size
        else:
            raise SystemExit(f"unexpected token {Byte:#04x} at {Index}")
    return Tokens


def Expand(Tokens: list[bytes], Budget: int) -> bytes:
    Out = b""
    Previous = b""
    for Token in Tokens:
        if Token[0] == 0xF6 or Token[0] == 0xF5 or Token[0] < 0xE4 or 0xE8 <= Token[0] <= 0xEB:
            Out += Token
            Previous = Token
        elif 0xE4 <= Token[0] <= 0xE7:
            Copies = Token[0] - 0xE3 if Token[0] != 0xE7 else Token[1]
            Added = Copies * len(Previous)
            if len(Out) + Added <= Budget:
                Out += Previous * Copies
            else:
                Out += Token
        else:
            raise SystemExit(f"unexpected token {Token.hex()}")
    return Out


Tokens = Tokenize(Elements)
print(f"tokens {len(Tokens)} element bytes {len(Elements)}")

for Budget in (0x1A0, 0x19F, 0x1A1):
    Layers = dict(Payload=Payload)
    New = Intro + Expand(Tokens, Budget - 4)
    Total = Spans[0][0] + len(New) + (len(Payload) - Spans[0][1])
    Bodies = Author.EmptyPartSections((923, 979, 917))
    Bodies["AllFeatur"] = Author.SectionValue(
        "AllFeatur",
        Payload[: Spans[0][0]] + New + Payload[Spans[0][1] :],
    )
    Name = f"lane_{Budget:03x}"
    Target = Path.home() / "Documents/creo-authored" / f"{Name}.prt"
    Target.write_bytes(Subset.Build(Source, Header.base, set(), Bodies))
    print(f"{Name}: lane {len(New)} bytes (budget {Budget}) payload -> {Total}")

# Also change one lane in a way that cannot be a mere re-encode: keep the size the same but set the
# declared element count one short, which tests whether the count is checked against the elements.
Short = Lane[:3] + b"\xfb" + Elements
Bodies = Author.EmptyPartSections((923, 979, 917))
Bodies["AllFeatur"] = Author.SectionValue(
    "AllFeatur", Payload[: Spans[0][0]] + Short + Payload[Spans[0][1] :]
)
Path.home().joinpath("Documents/creo-authored/lane_short.prt").write_bytes(
    Subset.Build(Source, Header.base, set(), Bodies)
)
print(f"lane_short: declared count 251, {len(Short)} bytes")
