from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass


# malformed ug part payloads need a distinct container failure
class PayloadError(ValueError):
    __slots__ = ()


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


# ug part payload state stays inert so parsing and section roles split cleanly
@DataClass(frozen=True, slots=True)
class NxPayload:
    data: bytes
    legacy: bool
    rows: tuple[SegmentRow, ...]
    sections: tuple[OmSection, ...]
    streams: tuple[NxStream, ...]

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
