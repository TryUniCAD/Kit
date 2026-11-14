from __future__ import annotations as Annotations

import struct as Struct

# the root object section is lanes then a table then an order array then records
KSlice = 0x30C
KOrderStart = 0x664
KGapStart = 0x9B8
KRecordCount = 214
KNames = b"\x77\x0fm_nextInstance"
KHeadTag = b"\x41\x00\x03\x03"
KAnchor = b"\xe0\x6a\xf8"
KUnset = b"\xff" * 7
KHeadPrefix = bytes.fromhex("0305020004050100")
KHeadSuffix = bytes.fromhex("80d5021304050100010180d5021380d6020000")


# the head record names the part and anchors the identity of the saved state
def HeadRecord(PartText: bytes, Identity: bytes = KUnset) -> bytes:
    if not PartText:
        raise ValueError("NX root head record requires a part text")
    if len(PartText) > 200:
        raise ValueError("NX root head record part text is too long")
    if len(Identity) != 7:
        raise ValueError("NX root head record identity must be seven bytes")
    return (
        KHeadTag
        + bytes([len(PartText) + 2])
        + PartText
        + b"\x00"
        + KHeadPrefix
        + KAnchor
        + Identity
        + KHeadSuffix
    )


# the section counts follow the part name so the object count is read directly
def ObjectCount(SectionBody: bytes) -> int:
    NameLength = int(Struct.unpack_from("<I", SectionBody, 0x25)[0])
    if not 0 < NameLength <= 255:
        raise ValueError("NX section part name length is invalid")
    Count = int(Struct.unpack_from("<I", SectionBody, 0x29 + NameLength)[0])
    if Count <= 0:
        raise ValueError("NX object section declares no objects")
    return Count


# the object table is the one monotonic run of body relative offsets of that size
def TableStart(SectionBody: bytes, Count: int) -> int:
    Limit = len(SectionBody) - 12
    for Start in range(0x100, Limit - 4 * Count):
        Values = [
            int(Struct.unpack_from("<I", SectionBody, Start + 4 * Index)[0])
            for Index in range(Count)
        ]
        if Values[0] <= 0 or Values[-1] >= Limit:
            continue
        if not all(Values[Index] < Values[Index + 1] for Index in range(Count - 1)):
            continue
        Follow = int(Struct.unpack_from("<I", SectionBody, Start + 4 * Count)[0])
        if Follow <= Count:
            return Start
    raise ValueError("NX object section carries no object table")


# the section pointer names the end of the middle so a resize shifts it
def MovePointer(Section: bytearray, Source: bytes) -> bytearray:
    NameLength = int(Struct.unpack_from("<I", Source, 0x25)[0])
    if not 0 < NameLength <= 255:
        raise ValueError("NX section part name length is invalid")
    PointerAt = 0x29 + NameLength + 32
    Pointer = int(Struct.unpack_from("<I", Source, PointerAt)[0])
    Struct.pack_into("<I", Section, PointerAt, Pointer + len(Section) - len(Source))
    return Section


# the record boundaries are read from the table which is body relative
def RecordsOf(SectionBody: bytes) -> tuple[int, list[int], list[bytes]]:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Records = [SectionBody[Begin:Finish] for Begin, Finish in zip(Starts, Stops)]
    return (TableAt, Starts, Records)


# the head tail carries document varints so only the body less shape is emitted
def ReplaceHead(SectionBody: bytes, PartText: bytes, Identity: bytes = KUnset) -> bytes:
    TableAt, Starts, Records = RecordsOf(SectionBody)
    Source = Records[0]
    Records[0] = HeadRecord(PartText, Identity)
    if len(Source) != len(Records[0]):
        Records[0] = Source
    TableEnd = TableAt + 4 * len(Records)
    OrderCount = int(Struct.unpack_from("<I", SectionBody, TableEnd)[0])
    OrderEnd = TableEnd + 4 + 4 * OrderCount
    if not OrderEnd < Starts[0] <= len(SectionBody) - 12:
        raise ValueError("NX object section order array is not well formed")
    Section = bytearray(SectionBody[:TableAt])
    Position = 0
    for Record in Records:
        Section.extend((Starts[0] + Position).to_bytes(4, "little"))
        Position += len(Record)
    Section.extend(SectionBody[TableEnd:OrderEnd])
    Section.extend(SectionBody[OrderEnd : Starts[0]])
    for Record in Records:
        Section.extend(Record)
    Section.extend(SectionBody[len(SectionBody) - 12 :])
    return bytes(MovePointer(Section, SectionBody))


__all__ = [
    "HeadRecord",
    "KAnchor",
    "KRecordCount",
    "MovePointer",
    "ObjectCount",
    "RecordsOf",
    "TableStart",
    "KUnset",
    "ReplaceHead",
]
