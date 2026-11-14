from __future__ import annotations as Annotations

import struct as Struct

# a part without a body always carries the same three construction objects
KNames = b"\x02\x18m_legacyInactiveModules\x81\x0c"
KFlags = bytes([2]) * 8 + bytes([1]) * 9
KCounter = 0x3D8
KZeros = 64
KObjects = 3
KOrder = (3, 1, 3, 4)
KObjectCount = 3
KMiddleLength = 356
KRootIndex = 3
KFeatureIndex = 4
KNameOffset = 0x29
KCountBytes = 32
KIdentityOffset = 0xCA
KVersion = b"NX 2506.9120 - External User Function"
KUnset = b"\xff" * 7
KAnchor = b"\xe0\x6a\xf8"
KHead = b"\x41\x00\x03\x05\x01\x00\x04\x05\x02\x00"
KHeadTail = bytes.fromhex("05021306020000")
KDescriptor = bytes.fromhex("0202ffffffffffffffffffff0041ffffffffff0600f0000101010000")
KRecordBody = bytes.fromhex(
    "0202ff0080cd0104012fa47ae147ae147bffffffffffff030844454c4554450000000001000107ffffffffffff00ffffffffffffffffff0000000000000000000000000001020100000089ca01010200a5a5b6010000ff00ff9fb3c01ffffe0100000101010102060101000001000000"
)


# the body less construction middle is one fixed preamble and three objects
def ConstructMiddle(
    BaseOffset: int, Identity: bytes = KUnset, Counter: int = KCounter
) -> bytes:
    if len(Identity) != 7:
        raise ValueError("NX construction identity must be seven bytes")
    HeadBytes = KHead + KAnchor + Identity + KHeadTail
    Anchor = (
        b"\x03\x01"
        + bytes([len(KVersion) + 2])
        + KVersion
        + b"\x00"
        + b"\x08SYSTEM\x00"
    )
    Preamble = KNames + KFlags + Counter.to_bytes(4, "little") + bytes(KZeros)
    Order = b"".join(Value.to_bytes(4, "little") for Value in KOrder)
    First = len(Preamble) + 4 * KObjects + len(Order) + len(Anchor)
    Offsets = [First, First + len(HeadBytes), First + len(HeadBytes) + len(KDescriptor)]
    Table = b"".join((BaseOffset + Offset).to_bytes(4, "little") for Offset in Offsets)
    return b"".join((Preamble, Table, Order, Anchor, HeadBytes, KDescriptor, Record()))


# the infrastructure record carries two counts that step by three with a body
def Record(First: int = 7, Second: int = 8) -> bytes:
    if not 0 <= First < 256 or not 0 <= Second < 256:
        raise ValueError("NX construction record counts must fit one byte")
    Value = bytearray(KRecordBody)
    Value[0x20] = First
    Value[0x43] = Second
    return bytes(Value)


# only the three object shape is generated and a body part is left untouched
def ObjectCount(SectionBody: bytes) -> int:
    NameLength = int(Struct.unpack_from("<I", SectionBody, 0x25)[0])
    if not 0 < NameLength <= 255:
        raise ValueError("NX section part name length is invalid")
    return int(Struct.unpack_from("<I", SectionBody, KNameOffset + NameLength)[0])


# the pointer field follows the part name and the eight section counts
def PointerOffset(SectionBody: bytes) -> int:
    NameLength = int(Struct.unpack_from("<I", SectionBody, 0x25)[0])
    if not 0 < NameLength <= 255:
        raise ValueError("NX section part name length is invalid")
    return KNameOffset + NameLength + KCountBytes


# adopting keeps the class lanes and replaces the middle and its pointer
def Adopt(SectionBody: bytes, Middle: bytes) -> bytes:
    Offset = PointerOffset(SectionBody)
    Pointer = int(Struct.unpack_from("<I", SectionBody, Offset)[0])
    if not 0 < Pointer <= len(SectionBody):
        raise ValueError("NX section pointer is outside the section")
    Start = Pointer - KMiddleLength
    if Start <= 0:
        raise ValueError("NX construction section middle start is invalid")
    Authored = bytearray(SectionBody[:Start])
    Authored.extend(Middle)
    Authored.extend(SectionBody[Pointer:])
    Struct.pack_into("<I", Authored, Offset, Start + len(Middle))
    return bytes(Authored)


__all__ = [
    "Adopt",
    "ConstructMiddle",
    "KCounter",
    "ObjectCount",
    "Record",
    "KUnset",
]
