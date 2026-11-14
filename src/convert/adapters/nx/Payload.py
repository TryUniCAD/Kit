from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass
import struct as Struct
import zlib as ZlibValue


# malformed ug part payloads need a distinct container failure
class PayloadError(ValueError):
    __slots__ = ()


# the compressed stream wrapper prefix uses the low bits as extension length
KWrapperMask = 0xC0000000

# the minimal wrapper marker uses an eight byte fixed header
KWrapperShort = 0x80000000

# the duplicate wrapper marker uses a fixed sixteen byte header
KWrapperDup = 0xA0000000

# the extended wrapper marker selects a fixed header by code and version
KWrapperLong = 0xC0000000

# inflated payloads stay bounded so corrupt streams cannot exhaust memory
KMaxInflated = 256 * 1024 * 1024


# one segment index row preserves the three little endian words
@DataClass(frozen=True, slots=True)
class SegmentRow:
    type_code: int
    subtype_code: int
    value: int


# one object model section retains its exact source bounds
@DataClass(frozen=True, slots=True)
class OmSection:
    offset: int
    body_offset: int
    size: int


# one inflated parasolid stream retains wrapper and source provenance
@DataClass(frozen=True, slots=True)
class NxStream:
    offset: int
    compressed: int
    inflated: bytes
    kind: str


# ug part payload parsing recovers sections and geometry without vendor code
class NxPayload:
    # parsing validates the segment index before scanning any payload bytes
    def __init__(self, DataValue: bytes) -> None:
        super().__init__()
        self.data = DataValue
        if len(DataValue) < 24:
            raise PayloadError("ug part payload is too short")
        self.legacy = DataValue.startswith(b"\x0d\x01UGII")
        if self.legacy:
            self.rows = ()
            self.sections = self.FindSections()
            self.streams = ()
            return
        Header = Struct.unpack_from("<III", DataValue, 12)
        if Header[0] != 1 or Header[1] != 1:
            raise PayloadError("ug part segment index header is invalid")
        EndValue = Header[2]
        if not 24 <= EndValue <= len(DataValue):
            raise PayloadError("ug part segment index length is invalid")
        if EndValue % 12:
            raise PayloadError("ug part segment index is not row aligned")
        self.rows = tuple(
            SegmentRow(*Struct.unpack_from("<III", DataValue, Offset))
            for Offset in range(0, EndValue, 12)
        )
        self.sections = self.FindSections()
        self.streams = self.FindStreams()

    # section discovery uses the exact signature and declared big endian size
    def FindSections(self) -> tuple[OmSection, ...]:
        Sections: list[OmSection] = []
        Position = 0
        while True:
            BodyOffset = self.data.find(b"OM\x01\x01", Position)
            if BodyOffset < 0:
                break
            Position = BodyOffset + 4
            Prefix = BodyOffset - 12
            Start = Prefix
            if Prefix >= 0 and self.data[Prefix : Prefix + 4] == b"\xff\xff\xff\xff":
                SizeValue = int.from_bytes(self.data[Prefix + 8 : Prefix + 12], "big")
            else:
                Prefix = BodyOffset - 16
                if (
                    Prefix < 0
                    or self.data[Prefix : Prefix + 4] != bytes.fromhex("c0d1f1ed")
                    or self.data[Prefix + 4 : Prefix + 8] != b"\xff\xff\xff\xff"
                ):
                    continue
                SizeValue = int.from_bytes(self.data[Prefix + 12 : Prefix + 16], "big")
                Start = Prefix
            EndValue = BodyOffset + SizeValue
            if SizeValue <= 0 or EndValue > len(self.data):
                continue
            Sections.append(OmSection(Start, BodyOffset, SizeValue))
        return tuple(Sections)

    # stream discovery validates complete zlib members and bounds inflation
    def FindStreams(self) -> tuple[NxStream, ...]:
        Streams: list[NxStream] = []
        Position = 24
        while Position < len(self.data) - 1:
            if self.data[Position] != 0x78:
                Position += 1
                continue
            Inflated, Used = InflateMember(self.data[Position:])
            if Inflated is None:
                Position += 1
                continue
            KindValue = "parasolid" if Inflated.startswith(b"PS") else "compressed"
            Streams.append(NxStream(Position, Used, Inflated, KindValue))
            Position += max(Used, 1)
        return tuple(Streams)

    # section class markers expose roles without claiming a complete record decode
    def SectionMarkers(self) -> tuple[str, ...]:
        Output: list[str] = []
        for Section in self.sections:
            Block = self.data[Section.body_offset : Section.body_offset + Section.size]
            for Marker in (
                b"UGS::Solid::Topol",
                b"UGS::FEATURE_RECORD",
                b"UGS::EXP_expression",
                b"UGS::OCC_instance",
                b"UGS::OM::SaveAuditTrail",
            ):
                if Marker in Block:
                    NameValue = Marker.decode("ascii")
                    if NameValue not in Output:
                        Output.append(NameValue)
        return tuple(Output)

    # compressed stream wrappers use the low bits as an extension byte length
    def WrapperLength(self, Offset: int) -> int | None:
        if Offset + 8 > len(self.data):
            return None
        Marker = Struct.unpack_from("<I", self.data, Offset)[0]
        Extension = Marker & 0x3FFFFFFF
        if Marker == KWrapperDup:
            return 16
        if Marker & KWrapperMask == KWrapperShort:
            return 8 + Extension
        if Marker & KWrapperMask == KWrapperLong:
            if Offset + 16 > len(self.data):
                return None
            Code = Struct.unpack_from("<I", self.data, Offset + 8)[0]
            Version = Struct.unpack_from("<H", self.data, Offset + 12)[0]
            return {(37, 4): 33, (45, 5): 45, (61, 4): 57}.get((Code, Version))
        return None


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
    Used = len(DataValue) - len(Decoder.unused_data)
    return (Output, Used)
