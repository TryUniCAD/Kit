from __future__ import annotations as Annotations

import struct as Struct

from convert.adapters.nx.Payload import NxPayload, OmSection
from convert.adapters.nx.PayloadReader import ReadPayload

# section prefixes carry the declared size either inline or after the toolkit magic
KPlainPrefix = 12
KMixedPrefix = 16
KToolkitMagic = bytes.fromhex("c0d1f1ed")
KIndexHeader = 24


# section replacement resizes a payload without trusting any stored offset
def ResizePayload(Payload: bytes, SectionBodies: list[bytes]) -> bytes:
    Parsed = ReadPayload(Payload)
    if Parsed.legacy:
        raise ValueError("NX payload section rewriting requires a modern payload")
    if len(SectionBodies) != len(Parsed.sections):
        raise ValueError("NX payload rewriting requires one body per section")
    Layout = PlanLayout(Payload, Parsed, SectionBodies)
    Output = bytearray(Payload[:KIndexHeader])
    Remap: dict[int, int] = {}
    Cursor = KIndexHeader
    for Section, SectionBody, Prefix, Start in Layout:
        Output.extend(Payload[Cursor:Start])
        Remap[Section.offset] = len(Output)
        Remap[Section.body_offset] = len(Output) + Prefix
        Remap[Section.body_offset + Section.size] = (
            len(Output) + Prefix + len(SectionBody)
        )
        WriteSectionMut(Output, Payload, Section, SectionBody, Prefix)
        Cursor = Section.body_offset + Section.size
        Remap[Cursor] = len(Output)
    Output.extend(Payload[Cursor:])
    Remap[len(Payload)] = len(Output)
    Remap[len(Payload) - 1] = len(Output) - 1
    Remap[len(Payload) - 2] = len(Output) - 2
    RewriteRowsMut(Output, Payload, Parsed, Remap)
    return bytes(Output)


# layout planning keeps section order and its original prefix width
def PlanLayout(
    Payload: bytes, Parsed: NxPayload, SectionBodies: list[bytes]
) -> list[tuple[OmSection, bytes, int, int]]:
    Result: list[tuple[OmSection, bytes, int, int]] = []
    for Index, Section in enumerate(Parsed.sections):
        Prefix = Section.body_offset - Section.offset
        if Prefix not in (KPlainPrefix, KMixedPrefix):
            raise ValueError("NX payload section prefix is not a known width")
        if Section.offset < KIndexHeader:
            raise ValueError("NX payload section overlaps the segment index")
        Result.append((Section, SectionBodies[Index], Prefix, Section.offset))
    return Result


# section writing preserves the original prefix shape and refreshes the size
def WriteSectionMut(
    Output: bytearray,
    Payload: bytes,
    Section: OmSection,
    SectionBody: bytes,
    Prefix: int,
) -> None:
    Start = Section.offset
    if Prefix == KPlainPrefix:
        Output.extend(Payload[Start : Start + 8])
        Output.extend(len(SectionBody).to_bytes(4, "big"))
    else:
        Output.extend(Payload[Start : Start + 12])
        Output.extend(len(SectionBody).to_bytes(4, "big"))
    Output.extend(SectionBody)


# row rewriting maps every stored boundary to its new position
def RewriteRowsMut(
    Output: bytearray,
    Payload: bytes,
    Parsed: NxPayload,
    Remap: dict[int, int],
) -> None:
    EndValue = Struct.unpack_from("<III", Payload, 12)[2]
    IndexRows = bytearray(Payload[:EndValue])
    for Offset in range(0, len(IndexRows) // 12 * 12, 12):
        for Field in range(3):
            Cursor = Offset + Field * 4
            Value = Struct.unpack_from("<I", IndexRows, Cursor)[0]
            if Value in Remap:
                Struct.pack_into("<I", IndexRows, Cursor, Remap[Value])
    Output[: len(IndexRows)] = IndexRows
