from __future__ import annotations as Annotations

from dataclasses import dataclass as DataClass

from convert.adapters.nx.HashXxh import HashXxh

# a class table entry carries a prefix two digests and a one byte tail
KNameDigestWidth = 4

# needed so klayout digest width stays a single named source for the nx adapter
KLayoutDigestWidth = 4

# needed so ktail width stays a single named source for the nx adapter
KTailWidth = 1


# one link of a class inheritance chain contributes a schema a class and a kind
@DataClass(frozen=True)
class ClassLink:
    Schema: str
    Name: str
    Kind: int


# the name digest is xxh32 over every link of the chain root first
def NameDigest(Links: tuple[ClassLink, ...]) -> int:
    if not Links:
        raise ValueError("NX class name digest needs at least one chain link")
    Stream = bytearray()
    for Entry in Links:
        if not Entry.Schema or not Entry.Name:
            raise ValueError("NX class chain link needs a schema and a class name")
        if not 0 <= Entry.Kind <= 0xFFFFFFFF:
            raise ValueError("NX class chain kind must fit four bytes")
        Stream.extend(Entry.Schema.encode("ascii"))
        Stream.extend(Entry.Name.encode("ascii"))
        Stream.extend(Entry.Kind.to_bytes(4, "little"))
    return HashXxh(bytes(Stream))


# the stored entry ends with the layout digest and the tail
def EntryParts(Entry: bytes, NameDigestValue: int) -> tuple[bytes, int, int]:
    Pattern = NameDigestValue.to_bytes(KNameDigestWidth, "little")
    Position = Entry.find(Pattern)
    if Position < 0:
        raise ValueError("NX class entry does not carry its name digest")
    TailAt = Position + KNameDigestWidth + KLayoutDigestWidth
    if TailAt + KTailWidth != len(Entry):
        raise ValueError("NX class entry does not carry a one byte tail")
    Layout = int.from_bytes(Entry[Position + KNameDigestWidth : TailAt], "little")
    return (Entry[:Position], Layout, Entry[TailAt])


# needed so all stays a single named source for the nx adapter
__all__ = [
    "ClassLink",
    "EntryParts",
    "NameDigest",
]
