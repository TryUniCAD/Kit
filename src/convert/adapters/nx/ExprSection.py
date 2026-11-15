from __future__ import annotations as Annotations

import struct as Struct

from convert.adapters.nx.ObjectSection import ValueWord

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


# a dimension part carries two default group tokens that do not vary
KGroupPair = bytes.fromhex(
    "0202010241040f44656661756c742047726f757000"
) + bytes.fromhex("040f44656661756c742047726f757000")


def GroupPair() -> bytes:
    return KGroupPair


# the occupancy object lists the allocated ids a dimension shape adds
KOccupancy = {
    3: bytes.fromhex(
        "100121ffffff434445464748494a4bff4c4dffffffffffffff4effffff4f50ffffff511021"
    )
}


# the occupancy frame follows the dimension count and the continuation count
def OccupancyMap(Dimensions: int) -> int:
    Needed = 5 * Dimensions + 2
    Size = 32
    while Size <= Needed:
        Size *= 2
    return Size


def ExprOccupancyFrame(Dimensions: int, Continuations: int) -> tuple[bytes, bytes]:
    if not 1 <= Dimensions <= 0x32:
        raise ValueError("NX occupancy needs one to fifty dimensions")
    if not 0 <= Continuations <= 5 * Dimensions:
        raise ValueError("NX occupancy continuation count is out of range")
    Map = OccupancyMap(Dimensions)
    Head = bytes([5 * Dimensions + 1, 0x01, Map + 1])
    Trailing = bytes([5 * Dimensions + Continuations + 1, Map + 1])
    return (Head, Trailing)


def ExprOccupancy(Dimensions: int) -> bytes:
    Object = KOccupancy.get(Dimensions)
    if Object is None:
        raise ValueError("NX occupancy object is only measured for three dimensions")
    return Object


# the names lane is a slot map of tokens whose width the lead byte fixes
KExpNames = b"\x0fEXP_lookup_exp\x11EXP_compare_exps\x10EXP_hash_string\x0dEXP_hash_exp"
KLaneValueSlots = 32
KLaneMapBase = 32
KTokenWidths = {0x8B: 2, 0x8C: 2, 0xC4: 4, 0xE0: 5}


def ReadLaneTokens(TokenArea: bytes) -> tuple[bytes, ...]:
    Tokens: list[bytes] = []
    Position = 0
    while Position < len(TokenArea):
        Marker = TokenArea[Position]
        if Marker == 1:
            Position += 1
            continue
        Width = KTokenWidths.get(Marker)
        if Width is None or Position + Width > len(TokenArea):
            raise ValueError("NX names lane label token is invalid")
        Tokens.append(TokenArea[Position : Position + Width])
        Position += Width
    return tuple(Tokens)


def ReadLane(Record: bytes) -> tuple[tuple[bytes, ...], bytes]:
    if b"EXP_lookup_exp" not in Record:
        raise ValueError("NX names lane has no known names")
    Count = Record[0]
    Split = Record.index(KExpNames) + len(KExpNames)
    if Record[Split : Split + 2] != b"\x01\x21":
        raise ValueError("NX names lane has no known split")
    Middle = Record.index(b"\x21", Split + 2)
    if Record[-2:] != bytes([Count, 0x21]):
        raise ValueError("NX names lane has no known terminator")
    Labels = ReadLaneTokens(Record[Split + 2 : Middle])
    if len(Labels) != Count - 1:
        raise ValueError("NX names lane label count disagrees with its head")
    ValueArea = Record[Middle + 1 : len(Record) - 2]
    Values = bytes(Sample for Sample in ValueArea if Sample != 0xFF)
    return (Labels, Values)


# the writer puts its tokens in one run from the first slot
def ExprLane(Labels: tuple[bytes, ...], Values: bytes) -> bytes:
    Count = len(Labels) + 1
    if not 1 <= len(Labels) <= 0xFE:
        raise ValueError("NX names lane needs one to 254 expressions")
    if len(Values) != len(Labels):
        raise ValueError("NX names lane needs one value byte per expression")
    if len(Values) > KLaneValueSlots:
        raise ValueError("NX names lane value map is full")
    Tokens = b"".join(Labels)
    for Token in Labels:
        if len(Token) != KTokenWidths.get(Token[0]):
            raise ValueError("NX names lane label token width is inconsistent")
    Output = bytearray([Count])
    Output.extend(KExpNames)
    Output.extend(b"\x01\x21")
    Output.extend(Tokens)
    Output.extend(bytes([1]) * (KLaneMapBase + 2 - Count))
    Output.extend(b"\x21")
    Output.extend(Values)
    Output.extend(b"\xff" * (KLaneValueSlots - len(Values)))
    Output.extend([Count, 0x21])
    return bytes(Output)


# the head tail names two ids that follow the last one for the object and dim counts
def ExprHeadTail(Objects: int, Dimensions: int) -> bytes:
    if Objects < 6 or Dimensions < 0:
        raise ValueError("NX head tail needs at least six objects and no negative dims")
    Following = Objects + Dimensions + 2
    if Following > 0xFD:
        raise ValueError("NX head tail ids must fit one byte")
    return (
        bytes([Following])
        + bytes.fromhex("0213")
        + bytes([Following + 1])
        + bytes.fromhex("020000")
    )


# a group value is a length byte a text and a terminator
KGroupHead = b"\x02\x02\x04\x0fDefault Group\x00"
KGroupTail = bytes.fromhex("003f0000")


def ReadGroupValues(Record: bytes) -> tuple[bytes, ...]:
    if not Record.startswith(KGroupHead):
        raise ValueError("NX group record has no known head")
    Prefix = len(KGroupHead) + len(KGroupTail)
    if len(Record) == Prefix:
        return ()
    if len(Record) < Prefix + 2 or Record[Prefix] != 1:
        raise ValueError("NX group record has no known value list")
    Values: list[bytes] = []
    Position = Prefix + 2
    while Position < len(Record):
        Width = Record[Position]
        if Width < 3 or Position + Width > len(Record):
            raise ValueError("NX group record value length is out of range")
        if Record[Position + Width - 1] != 0:
            raise ValueError("NX group record value is not terminated")
        Values.append(Record[Position + 1 : Position + Width - 1])
        Position += Width
    return tuple(Values)


def GroupRecord(Values: tuple[bytes, ...]) -> bytes:
    Output = bytearray(KGroupHead + KGroupTail)
    if not Values:
        return bytes(Output)
    Output.append(1)
    if len(Values) > 0xFE:
        raise ValueError("NX group record value count must fit one byte")
    Output.append(len(Values) + 1)
    for ValueText in Values:
        if not ValueText or b"\x00" in ValueText or len(ValueText) > 0xFD:
            raise ValueError("NX group record value must be a non empty text")
        Output.append(len(ValueText) + 2)
        Output.extend(ValueText)
        Output.append(0)
    return bytes(Output)


# the preamble counts objects and carries a word at offset 48 for large shapes
def ExprPreamble(Objects: int, Pointer: int, Extra: int = 0) -> bytes:
    if Objects < KObjects:
        raise ValueError("NX expression section needs at least six objects")
    if not 0 < Pointer < 1 << 32:
        raise ValueError("NX expression pointer must fit four bytes")
    Groups = -(-Objects // KObjects)
    Flags = 4 if Objects == KObjects else 7
    Padding = bytearray(bytes(KZeros))
    if Extra:
        Padding[0x30 - 9 - Flags - 4 : 0x34 - 9 - Flags - 4] = Extra.to_bytes(
            4, "little"
        )
    return (
        bytes([2]) * 7
        + bytes([Objects - 5, Groups])
        + bytes([1]) * Flags
        + Pointer.to_bytes(4, "little")
        + bytes(Padding)
    )


# order entries are ids so the writer emits one through n
def ExprOrder(Objects: int) -> bytes:
    if Objects < 1:
        raise ValueError("NX expression order needs at least one object")
    return Objects.to_bytes(4, "little") + b"".join(
        Index.to_bytes(4, "little") for Index in range(1, Objects + 1)
    )


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


# a value slot carries the expression value in a four byte word instead of a handle
def ValueSlot(Value: float) -> bytes:
    return KSlotHead + KSlotFlags + ValueWord(Value) + bytes(2) + b"\xff"


def ReadValueSlot(Object: bytes) -> int:
    if len(Object) != 21 or not Object.startswith(KSlotHead):
        raise ValueError("NX value slot has no known frame")
    return int.from_bytes(Object[14:16], "little")


def ReadSlotHandle(Object: bytes) -> int:
    if len(Object) != 18 or not Object.startswith(KSlotHead):
        raise ValueError("NX slot object has no known frame")
    return int.from_bytes(Object[14:17], "little")


# a block part adds five property slots and one record for each of its expressions
def ExprObjectCount(Dimensions: int) -> int:
    if Dimensions < 0:
        raise ValueError("NX dimension count must not be negative")
    return KObjects + 6 * Dimensions


# a dimension part carries two value slots and one plain slot per dimension plus one
def ValueSlotCount(Dimensions: int) -> int:
    if Dimensions < 1:
        raise ValueError("NX dimension count must be at least one")
    return 2 * Dimensions - 1


# a writer may choose the object order so the layout is fixed here once
def ExprLayout(Dimensions: int) -> tuple[str, ...]:
    if Dimensions < 0:
        raise ValueError("NX dimension count must not be negative")
    if Dimensions == 0:
        return ("head", "descriptor", "names", "lane", "group", "record")
    Layout: list[str] = [
        "head",
        "descriptor",
        "names",
        "occupancy",
        "group",
        "group-record",
    ]
    for _ in range(Dimensions - 1):
        Layout.extend(["value", "plain", "plain", "value", "plain"])
    Layout.extend(["value", "plain", "plain", "plain", "plain"])
    Layout.extend(["record"] * Dimensions)
    return tuple(Layout)


def PlainSlotCount(Dimensions: int) -> int:
    if Dimensions < 1:
        raise ValueError("NX dimension count must be at least one")
    return 3 * Dimensions + 1


# the expression section middle is a fixed layout of six objects
def ExprMiddle(BaseOffset: int, Identity: bytes = KUnset) -> bytes:
    if len(Identity) != 7:
        raise ValueError("NX expression identity must be seven bytes")
    HeadBytes = KHead + KAnchor + Identity + ExprHeadTail(KObjects, 0)
    Version = VersionBlock()
    Preamble = ExprPreamble(KObjects, BaseOffset + 0x79)
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
    "ExprLayout",
    "ExprOrder",
    "ExprPreamble",
    "GroupPair",
    "ExprObjectCount",
    "PlainSlotCount",
    "ValueSlotCount",
    "ReadSlotHandle",
    "ReadValueSlot",
    "RewriteSlots",
    "SlotObject",
    "ValueSlot",
    "ExprMiddle",
    "KMiddleLength",
    "KObjects",
    "PointerOffset",
]


# slot objects in an expression section are rewritten from their handles
def RewriteSlots(SectionBody: bytes) -> bytes:
    if not SectionBody.startswith(b"OM\x01\x01"):
        return SectionBody
    NameLength = int(Struct.unpack_from("<I", SectionBody, 0x25)[0])
    if not 0 < NameLength <= 255:
        return SectionBody
    PointerAt = 0x29 + NameLength + 32
    Pointer = int(Struct.unpack_from("<I", SectionBody, PointerAt)[0])
    if not 0 < Pointer <= len(SectionBody) - 12:
        return SectionBody
    TableAt = Pointer - KMiddleLength + 0x54
    Count = int(Struct.unpack_from("<I", SectionBody, TableAt - 4)[0])
    if not 0 < Count <= 64:
        return SectionBody
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    if Starts[0] >= Pointer:
        return SectionBody
    Stops = Starts[1:] + [Pointer]
    Section = bytearray(SectionBody)
    for Begin, Finish in zip(Starts, Stops):
        Length = Finish - Begin
        Object = SectionBody[Begin:Finish]
        if Length == 18 and Object.startswith(bytes.fromhex("02020000ff000021")):
            Section[Begin:Finish] = SlotObject(ReadSlotHandle(Object))
        elif Length == 21 and Object.startswith(bytes.fromhex("02020000ff000021")):
            Section[Begin:Finish] = ValueSlot(ReadValueSlot(Object))
    return bytes(Section)
