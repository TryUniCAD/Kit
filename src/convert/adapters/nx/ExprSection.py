from __future__ import annotations as Annotations

import struct as Struct

# a part without expressions carries one fixed expression section middle
KVersion = b"NX 2506.9120 - External User Function"
KFlags = bytes([2]) * 7 + bytes([1]) * 6
KZeros = 52
KObjects = 6
KOrder = (1, 3, 5, 4, 6, 7)
KMiddleLength = 337
KAnchor = b"\xe0\x6a\xf8"
KUnset = b"\xff" * 7
KHead = b"\x41\x00\x03\x05\x01\x00\x04\x05\x02\x00"
KHeadTail = bytes.fromhex("08021309020000")
KDescriptor = bytes.fromhex("0202ffffff41ff4200ff000000430000ff010101011e01000101")
KNames = bytes.fromhex(
    "010f4558505f6c6f6f6b75705f657870114558505f636f6d706172655f65787073104558505f686173685f737472696e670d4558505f686173685f65787000000121"
)
KLane = bytes.fromhex("01000111")
KGroup = b"\x02\x02\x01\x02\x41\x00\x04\x0fDefault Group\x00"
KRecord = b"\x02\x02\x04\x0fDefault Group\x00\x00\x3f\x00\x00"


# the version block names the modeller and the system user that saved the part
def VersionBlock() -> bytes:
    return (
        b"\x03\x01"
        + bytes([len(KVersion) + 2])
        + KVersion
        + b"\x00"
        + b"\x08SYSTEM\x00"
    )


# a slot object is a fixed frame five flags a handle and a terminator
KSlotHead = bytes.fromhex("02020000ff000021")
KSlotFlags = bytes([1]) * 5 + bytes(1)


def SlotObject(Handle: int) -> bytes:
    if not 0 <= Handle <= 0xFFFFFF:
        raise ValueError("NX slot handle must fit three bytes")
    return KSlotHead + KSlotFlags + Handle.to_bytes(3, "little") + b"\xff"


def ReadSlotHandle(Object: bytes) -> int:
    if len(Object) != 18 or not Object.startswith(KSlotHead):
        raise ValueError("NX slot object has no known frame")
    return int.from_bytes(Object[14:17], "little")


# a block part adds five property slots and one record for each of its expressions
def ExprObjectCount(Expressions: int) -> int:
    if Expressions < 0:
        raise ValueError("NX expression count must not be negative")
    return KObjects + 6 * Expressions


# the expression section middle is a fixed layout of six objects
def ExprMiddle(BaseOffset: int, Identity: bytes = KUnset) -> bytes:
    if len(Identity) != 7:
        raise ValueError("NX expression identity must be seven bytes")
    HeadBytes = KHead + KAnchor + Identity + KHeadTail
    Version = VersionBlock()
    Preamble = KFlags + (BaseOffset + 0x79).to_bytes(4, "little") + bytes(KZeros)
    Order = (KObjects).to_bytes(4, "little") + b"".join(
        Value.to_bytes(4, "little") for Value in KOrder
    )
    First = len(Preamble) + 4 * KObjects + len(Order) + len(Version)
    Offsets = [
        First,
        First + len(HeadBytes),
        First + len(HeadBytes) + len(KDescriptor),
        First + len(HeadBytes) + len(KDescriptor) + len(KNames),
        First + len(HeadBytes) + len(KDescriptor) + len(KNames) + len(KLane),
        First
        + len(HeadBytes)
        + len(KDescriptor)
        + len(KNames)
        + len(KLane)
        + len(KGroup),
    ]
    Table = b"".join((BaseOffset + Offset).to_bytes(4, "little") for Offset in Offsets)
    return b"".join(
        (
            Preamble,
            Table,
            Order,
            Version,
            HeadBytes,
            KDescriptor,
            KNames,
            KLane,
            KGroup,
            KRecord,
        )
    )


# the section pointer field follows the part name and the eight section counts
def PointerOffset(SectionBody: bytes) -> int:
    NameLength = int(Struct.unpack_from("<I", SectionBody, 0x25)[0])
    if not 0 < NameLength <= 255:
        raise ValueError("NX section part name length is invalid")
    return 0x29 + NameLength + 32


# a generated middle replaces the source middle and refreshes the section pointer
def Adopt(SectionBody: bytes, Middle: bytes) -> bytes:
    Offset = PointerOffset(SectionBody)
    Pointer = int(Struct.unpack_from("<I", SectionBody, Offset)[0])
    if not 0 < Pointer <= len(SectionBody):
        raise ValueError("NX section pointer is outside the section")
    Start = Pointer - KMiddleLength
    if Start <= 0:
        raise ValueError("NX expression section middle start is invalid")
    Authored = bytearray(SectionBody[:Start])
    Authored.extend(Middle)
    Authored.extend(SectionBody[Pointer:])
    Struct.pack_into("<I", Authored, Offset, Start + len(Middle))
    return bytes(Authored)


__all__ = [
    "Adopt",
    "ExprObjectCount",
    "ReadSlotHandle",
    "SlotObject",
    "ExprMiddle",
    "KMiddleLength",
    "KObjects",
    "PointerOffset",
]
