from __future__ import annotations as Annotations
import struct as Struct
import zlib as ZlibValue

from convert.adapters.nx.Payload import (
    NxPayload,
    NxStream,
    OmSection,
    PayloadError,
    SegmentRow,
)

# inflated payloads stay bounded so corrupt streams cannot exhaust memory
KMaxInflated = 256 * 1024 * 1024


# payload parsing validates the segment index before scanning any payload bytes
def ReadPayload(DataValue: bytes) -> NxPayload:
    if len(DataValue) < 24:
        raise PayloadError("ug part payload is too short")
    Sections = FindSections(DataValue)
    if DataValue.startswith(b"\x0d\x01UGII"):
        return NxPayload(DataValue, True, (), Sections, ())
    Header = Struct.unpack_from("<III", DataValue, 12)
    if Header[0] != 1 or Header[1] != 1:
        raise PayloadError("ug part segment index header is invalid")
    EndValue = Header[2]
    if not 24 <= EndValue <= len(DataValue) or EndValue % 12:
        raise PayloadError("ug part segment index length is invalid")
    RowValues = tuple(
        SegmentRow(*Struct.unpack_from("<III", DataValue, Offset))
        for Offset in range(0, EndValue, 12)
    )
    return NxPayload(DataValue, False, RowValues, Sections, FindStreams(DataValue))


# section discovery uses the exact signature and declared big endian size
def FindSections(DataValue: bytes) -> tuple[OmSection, ...]:
    Sections: list[OmSection] = []
    Position = 0
    while True:
        BodyOffset = DataValue.find(b"OM\x01\x01", Position)
        if BodyOffset < 0:
            break
        Position = BodyOffset + 4
        Section = ReadSection(DataValue, BodyOffset)
        if Section is not None:
            Sections.append(Section)
    return tuple(Sections)


# one section validates its optional separator before accepting a size
def ReadSection(DataValue: bytes, BodyOffset: int) -> OmSection | None:
    Prefix = BodyOffset - 12
    Start = Prefix
    if Prefix >= 0 and DataValue[Prefix : Prefix + 4] == b"\xff\xff\xff\xff":
        SizeValue = int.from_bytes(DataValue[Prefix + 8 : Prefix + 12], "big")
    else:
        Prefix = BodyOffset - 16
        if (
            Prefix < 0
            or DataValue[Prefix : Prefix + 4] != bytes.fromhex("c0d1f1ed")
            or DataValue[Prefix + 4 : Prefix + 8] != b"\xff\xff\xff\xff"
        ):
            return None
        SizeValue = int.from_bytes(DataValue[Prefix + 12 : Prefix + 16], "big")
        Start = Prefix
    EndValue = BodyOffset + SizeValue
    if SizeValue <= 0 or EndValue > len(DataValue):
        return None
    return OmSection(Start, BodyOffset, SizeValue)


# stream discovery validates complete zlib members and bounds inflation
def FindStreams(DataValue: bytes) -> tuple[NxStream, ...]:
    Streams: list[NxStream] = []
    Position = 24
    while Position < len(DataValue) - 1:
        if DataValue[Position] != 0x78:
            Position += 1
            continue
        Inflated, UsedBytes = InflateMember(DataValue[Position:])
        if Inflated is None:
            Position += 1
            continue
        KindValue = "parasolid" if Inflated.startswith(b"PS") else "compressed"
        Streams.append(NxStream(Position, UsedBytes, Inflated, KindValue))
        Position += max(UsedBytes, 1)
    return tuple(Streams)


# inflation accepts only complete members and rejects oversized payloads
def InflateMember(DataValue: bytes) -> tuple[bytes | None, int]:
    try:
        Decoder = ZlibValue.decompressobj()
        Output = Decoder.decompress(DataValue, KMaxInflated + 1)
        Output += Decoder.flush()
    except ZlibValue.error:
        return (None, 0)
    if not Decoder.eof or len(Output) > KMaxInflated:
        return (None, 0)
    UsedBytes = len(DataValue) - len(Decoder.unused_data)
    return (Output, UsedBytes)
