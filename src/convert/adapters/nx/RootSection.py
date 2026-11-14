from __future__ import annotations as Annotations

import struct as Struct

from convert.adapters.nx.Payload import NxPayload
from convert.adapters.nx.Construction import (
    Adopt,
    ConstructMiddle,
    KMiddleLength,
    ObjectCount,
)
from convert.adapters.nx.ExprSection import (
    Adopt as AdoptExpr,
)
from convert.adapters.nx.ExprSection import (
    ExprMiddle,
    KMiddleLength as KExprMiddle,
    KObjects as KExprObjects,
)
from convert.adapters.nx.ObjectSection import (
    RelabelLanes,
    RelabelRefs,
    RelabelTokens,
    ReplaceHead,
    RewriteRecords,
    RewriteValues,
)
from convert.adapters.nx.PayloadBuild import ResizePayload
from convert.adapters.nx.PayloadReader import ReadPayload

# the root section middle is a fixed layout around a counter and an anchor identity
KVersion = b"NX 2506.9120 - External User Function"
KAnchor = b"\xe0\x6a\xf8"
KUnset = b"\xff" * 7
KCounterGap = 49
KCounterTail = 76
KRootCounter = 0x1E3
KRootMiddle = 176
KRootIndex = 3
KFeatureIndex = 4
KFeatureStub = b"OM\x01\x01"
KNameOffset = 0x29
KCountBytes = 32
KDeltaId = bytes.fromhex(
    "040213050200000202ffff00ffff000000ffffffff0000ff00ffffffffff0000ff00ffff00ffff00ff0101"
)


# the root middle carries one counter and one seven byte saved pointer
def RootMiddle(Counter: int, Identity: bytes) -> bytes:
    if len(Identity) != 7:
        raise ValueError("NX root section identity must be seven bytes")
    if Counter <= 0:
        raise ValueError("NX root section counter must be positive")
    return b"".join(
        (
            bytes([2, 2, 2, 1, 1, 1, 1, 1]),
            Counter.to_bytes(4, "little"),
            bytes(0x20),
            (Counter + KCounterGap).to_bytes(4, "little"),
            (Counter + KCounterTail).to_bytes(4, "little"),
            (2).to_bytes(4, "little"),
            (1).to_bytes(4, "little"),
            (3).to_bytes(4, "little"),
            b"\x03\x01" + bytes([len(KVersion) + 2]),
            KVersion,
            b"\x00",
            b"\x08SYSTEM\x00",
            b"\x41\x00",
            b"\x03\x05\x01\x00",
            b"\x04\x05\x02\x00",
            KAnchor,
            Identity,
            KDeltaId,
        )
    )


# the section pointer marks the end of the middle when no records follow
def MiddleStart(SectionBody: bytes, Pointer: int) -> int:
    if not 0 < Pointer <= len(SectionBody):
        raise ValueError("NX root section pointer is outside the section")
    Start = Pointer - KRootMiddle
    if Start <= 0 or Start >= Pointer:
        raise ValueError("NX root section does not carry a known middle")
    return Start


# the pointer field follows the part name and the eight section counts
def PointerOffset(SectionBody: bytes) -> int:
    NameLength = int(Struct.unpack_from("<I", SectionBody, 0x25)[0])
    if not 0 < NameLength <= 255:
        raise ValueError("NX section part name length is invalid")
    return KNameOffset + NameLength + KCountBytes


# authored sections regenerate the root middle and empty the feature record
def AuthorSections(Payload: bytes, HeadText: bytes | None = None) -> bytes:
    Parsed = ReadPayload(Payload)
    if Parsed.legacy:
        raise ValueError("NX authored sections require a modern payload")
    if len(Parsed.sections) <= KRootIndex:
        raise ValueError("NX authored sections require a root section")
    Section = Parsed.sections[KRootIndex]
    SectionBody = Payload[Section.body_offset : Section.body_offset + Section.size]
    Offset = PointerOffset(SectionBody)
    Pointer = Struct.unpack_from("<I", SectionBody, Offset)[0]
    Start = MiddleStart(SectionBody, Pointer)
    Counter = int.from_bytes(SectionBody[Start + 0x08 : Start + 0x0C], "little")
    Middle = RootMiddle(Counter, KUnset)
    Authored = bytearray(SectionBody[:Start])
    Authored.extend(Middle)
    Authored.extend(SectionBody[Pointer:])
    Struct.pack_into("<I", Authored, Offset, Start + len(Middle))
    return WithStub(Payload, Parsed, bytes(Authored), HeadText)


# every section anchors its saved state on one seven byte identity after e0 6a f8
def PatchAnchor(SectionBody: bytes, Identity: bytes = KUnset) -> bytes:
    if len(Identity) != 7:
        raise ValueError("NX section identity must be seven bytes")
    Value = bytearray(SectionBody)
    AnchorAt = Value.find(KAnchor)
    if AnchorAt < 0:
        raise ValueError("NX section body carries no anchor")
    Value[AnchorAt + len(KAnchor) : AnchorAt + len(KAnchor) + len(Identity)] = Identity
    return bytes(Value)


# the payload must end at the last section body because trailing bytes are refused
def WithStub(
    Payload: bytes, Parsed: NxPayload, RootBody: bytes, HeadText: bytes | None
) -> bytes:
    Bodies: list[bytes] = []
    for Index, Section in enumerate(Parsed.sections):
        SectionBody = Payload[Section.body_offset : Section.body_offset + Section.size]
        if Index == 0 and HeadText is not None:
            SectionBody = ReplaceHead(SectionBody, HeadText)
            SectionBody = RelabelTokens(
                RelabelLanes(RelabelRefs(RewriteValues(RewriteRecords(SectionBody))))
            )
        elif Index == KRootIndex:
            SectionBody = RootBody
        elif Index == KFeatureIndex and Index < len(Parsed.sections):
            SectionBody = KFeatureStub
        elif Index == 1 and ObjectCount(SectionBody) == 3:
            Pointer = int(
                Struct.unpack_from("<I", SectionBody, PointerOffset(SectionBody))[0]
            )
            Start = Pointer - KMiddleLength
            Counter = int.from_bytes(SectionBody[Start + 0x2C : Start + 0x30], "little")
            SectionBody = Adopt(SectionBody, ConstructMiddle(Start, Counter=Counter))
        elif Index == 2 and ObjectCount(SectionBody) == KExprObjects:
            Pointer = int(
                Struct.unpack_from("<I", SectionBody, PointerOffset(SectionBody))[0]
            )
            SectionBody = AdoptExpr(SectionBody, ExprMiddle(Pointer - KExprMiddle))
        elif Index == 2:
            SectionBody = PatchAnchor(SectionBody)
        Bodies.append(SectionBody)
    Resized = ResizePayload(Payload, Bodies)
    EndValue = ReadPayload(Resized).sections[-1]
    return Resized[: EndValue.body_offset + EndValue.size]
