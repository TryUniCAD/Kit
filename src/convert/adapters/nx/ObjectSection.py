from __future__ import annotations as Annotations

import struct as Struct

from convert.adapters.nx.ExprValue import EncodeValue

# the root object section is lanes then a table then an order array then records
KSlice = 0x30C

# needed so korder start stays a single named source for the nx adapter
KOrderStart = 0x664

# needed so kgap start stays a single named source for the nx adapter
KGapStart = 0x9B8

# needed so krecord count stays a single named source for the nx adapter
KRecordCount = 214

# needed so kinstance sizes stays a single named source for the nx adapter
KInstanceSizes = (27, 34, 48)

# needed so kreference tags stays a single named source for the nx adapter
KReferenceTags = (0x30, 0xB0)

# needed so kinstance frame stays a single named source for the nx adapter
KInstanceFrame = b"\x00\xf0"

# needed so kinstance class stays a single named source for the nx adapter
KInstanceClass = b"\xc0\x45"

# needed so kreference stays a single named source for the nx adapter
KReference = 7

# needed so kinstance skip stays a single named source for the nx adapter
KInstanceSkip = 21

# needed so knames stays a single named source for the nx adapter
KNames = b"\x77\x0fm_nextInstance"

# needed so khead tag stays a single named source for the nx adapter
KHeadTag = b"\x41\x00\x03\x03"

# needed so kanchor stays a single named source for the nx adapter
KAnchor = b"\xe0\x6a\xf8"

# needed so kunset stays a single named source for the nx adapter
KUnset = b"\xff" * 7

# needed so khead prefix stays a single named source for the nx adapter
KHeadPrefix = bytes.fromhex("0305020004050100")

# needed so khead suffix stays a single named source for the nx adapter
KHeadSuffix = bytes.fromhex("80d5021304050100010180d5021380d6020000")

# needed so khead suffix tail stays a single named source for the nx adapter
KHeadSuffixTail = bytes.fromhex("13040501000101")

# needed so khead suffix end stays a single named source for the nx adapter
KHeadSuffixEnd = bytes.fromhex("0000")


# the head suffix names the next object id twice and the id after it once
def HeadSuffix(NextId: int) -> bytes:
    if not 0 < NextId < 0x10000:
        raise ValueError("NX root head record next id is out of range")
    Low = (NextId - 1) & 0xFF
    return (
        bytes([0x80, Low, 0x02])
        + KHeadSuffixTail
        + bytes([0x80, Low, 0x02, 0x13, 0x80, NextId & 0xFF, 0x02])
        + KHeadSuffixEnd
    )


# the head record names the part and anchors the identity of the saved state
def HeadRecord(
    PartText: bytes,
    Identity: bytes = KUnset,
    Suffix: bytes = KHeadSuffix,
) -> bytes:
    if not PartText:
        raise ValueError("NX root head record requires a part text")
    if len(PartText) > 200:
        raise ValueError("NX root head record part text is too long")
    if len(Identity) not in (6, 7):
        raise ValueError("NX root head record identity must be six or seven bytes")
    if len(Suffix) != 19:
        raise ValueError("NX root head record suffix must be nineteen bytes")
    return (
        KHeadTag
        + bytes([len(PartText) + 2])
        + PartText
        + b"\x00"
        + KHeadPrefix
        + KAnchor
        + Identity
        + Suffix
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


# a record keeps the source length so the text is fitted into the same frame
def FitText(PartText: bytes, Length: int) -> bytes:
    if Length <= 0:
        raise ValueError("NX root head record has no room for a text")
    Prefix = b'Part renamed from "'
    if PartText.startswith(Prefix) and PartText.endswith(b'"'):
        PartText = PartText[len(Prefix) : -1]
    return PartText[:Length].ljust(Length, b" ")


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


# the head keeps the source identity because a saved pointer is document bound
def HeadParts(Source: bytes) -> tuple[bytes, bytes]:
    AnchorAt = Source.find(KAnchor)
    if AnchorAt < 0:
        raise ValueError("NX root head record carries no anchor")
    Begin = AnchorAt + 3
    for Position in range(Begin, len(Source) - 8):
        if (
            Source[Position] == 0x80
            and Source[Position + 2] == 0x02
            and Source[Position + 3] == 0x13
            and Source[Position + 4 : Position + 8] == b"\x04\x05\x01\x00"
        ):
            return (Source[Begin:Position], Source[Position:])
    raise ValueError("NX root head record carries no suffix")


# the head keeps the source identity because a saved pointer is document bound
def ReplaceHead(
    SectionBody: bytes, PartText: bytes, Identity: bytes | None = None
) -> bytes:
    TableAt, Starts, Records = RecordsOf(SectionBody)
    Source = Records[0]
    Saved, Suffix = HeadParts(Source)
    if Identity is not None:
        Saved = Identity
    Reserve = 36 + len(Saved)
    Emitted = HeadRecord(FitText(PartText, len(Source) - Reserve), Saved, Suffix)
    Records[0] = Emitted if Emitted == Source else Source
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


# needed so all stays a single named source for the nx adapter
__all__ = [
    "RewriteNesting",
    "NestingRecord",
    "ReadNesting",
    "ReadSmallRecord",
    "SmallRecord",
    "RewriteValues",
    "RewriteWordRun",
    "FloatWord",
    "ReadFloatWord",
    "ReadValueWord",
    "ValueWord",
    "RenameView",
    "ViewName",
    "LaneParts",
    "LaneRecord",
    "RelabelLanes",
    "RelabelTokens",
    "ParseSlots",
    "SlotPrefix",
    "SlotRecord",
    "RelabelRefs",
    "RewriteRecords",
    "PairRecord",
    "AttributeRecord",
    "HeadRecord",
    "HeadSuffix",
    "HeadParts",
    "KHeadSuffix",
    "KAnchor",
    "KRecordCount",
    "FitText",
    "MovePointer",
    "ObjectCount",
    "ParseAttribute",
    "ParsePair",
    "ReadToken",
    "RecordsOf",
    "RegToken",
    "TableStart",
    "KUnset",
    "ReplaceHead",
]


# an attribute record is a key and value pair followed by an ordinal and a terminator
def AttributeRecord(
    KeyText: bytes, ValueText: bytes, Ordinal: int, Marker: int = 1
) -> bytes:
    if len(KeyText) > 253 or len(ValueText) > 253:
        raise ValueError("NX attribute record text is too long")
    if not 0 <= Ordinal <= 255:
        raise ValueError("NX attribute record ordinal must fit one byte")
    if Marker not in (0, 1):
        raise ValueError("NX attribute record flag must be zero or one")
    return (
        b"\x01\x02\x04"
        + bytes([len(KeyText) + 2])
        + KeyText
        + b"\x00"
        + b"\x01\x02\x04"
        + bytes([len(ValueText) + 2])
        + ValueText
        + b"\x00"
        + bytes([Ordinal, Marker])
    )


# the attribute grammar reads back as the same three fields it writes
def ParseAttribute(Record: bytes) -> tuple[bytes, bytes, int, int]:
    if Record[:3] != b"\x01\x02\x04":
        raise ValueError("NX attribute record has no key marker")
    KeyLength = Record[3] - 2
    if KeyLength < 0:
        raise ValueError("NX attribute record key length is invalid")
    KeyText = Record[4 : 4 + KeyLength]
    ValueAt = 4 + KeyLength
    if Record[ValueAt] != 0 or Record[ValueAt + 1 : ValueAt + 4] != b"\x01\x02\x04":
        raise ValueError("NX attribute record key is not terminated")
    ValueLength = Record[ValueAt + 4] - 2
    if ValueLength < 0:
        raise ValueError("NX attribute record value length is invalid")
    ValueText = Record[ValueAt + 5 : ValueAt + 5 + ValueLength]
    EndAt = ValueAt + 5 + ValueLength
    if (
        Record[EndAt] != 0
        or len(Record) != EndAt + 3
        or Record[EndAt + 2] not in (0, 1)
    ):
        raise ValueError("NX attribute record value is not terminated")
    return (KeyText, ValueText, Record[EndAt + 1], Record[EndAt + 2])


# a pair record is a fixed frame with two registry tokens and absent slot runs
KPairFrame = bytes.fromhex(
    "0311030111010101010101010201010101010101010102e0555595560111"
)

# needed so kpair gap stays a single named source for the nx adapter
KPairGap = bytes([0xFF]) * 6

# needed so kpair tail stays a single named source for the nx adapter
KPairTail = bytes([0xFF]) * 8


# registry tokens store up to 0x7f directly and larger values behind a 0x80 prefix
def RegToken(Value: int) -> bytes:
    if not 0 <= Value <= 0x7FFF:
        raise ValueError("NX registry token is out of range")
    if Value <= 0x7F:
        return bytes([Value])
    return bytes([0x80 | (Value >> 8), Value & 0xFF])


# needed so read token keeps its nx behaviour in one reviewable place
def ReadToken(Stream: bytes, Position: int) -> tuple[int, int]:
    Prefix = Stream[Position]
    if Prefix <= 0x7F:
        return (Prefix, 1)
    if 0x80 <= Prefix <= 0x8F and Position + 1 < len(Stream):
        return (((Prefix & 0x0F) << 8) | Stream[Position + 1], 2)
    raise ValueError("NX registry token is invalid")


# a pair record names two adjacent object ids
def PairRecord(First: int, Second: int) -> bytes:
    return KPairFrame + RegToken(First) + KPairGap + RegToken(Second) + KPairTail


# the pair grammar reads back as the two ids it writes
def ParsePair(Record: bytes) -> tuple[int, int]:
    if not Record.startswith(KPairFrame):
        raise ValueError("NX pair record has no known frame")
    First, Width = ReadToken(Record, len(KPairFrame))
    GapAt = len(KPairFrame) + Width
    if Record[GapAt : GapAt + len(KPairGap)] != KPairGap:
        raise ValueError("NX pair record gap is not absent slots")
    Second, Width = ReadToken(Record, GapAt + len(KPairGap))
    TailAt = GapAt + len(KPairGap) + Width
    if Record[TailAt:] != KPairTail:
        raise ValueError("NX pair record tail is not absent slots")
    return (First, Second)


# the decoded families take any value so the writer assigns its own labels
def RewriteRecords(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Section = bytearray(SectionBody)
    Ordinal = 1
    Label = 1
    for Begin, Finish in zip(Starts, Stops):
        Record = bytes(SectionBody[Begin:Finish])
        if Record[:3] == b"\x01\x02\x04":
            KeyText, ValueText, _, Marker = ParseAttribute(Record)
            Written = AttributeRecord(KeyText, ValueText, Ordinal & 0x3F, Marker)
            Ordinal += 1
        elif Record[:2] == b"\x02\x02" and Record[3] == 0 and Record[4] == 0x36:
            try:
                Tokens = ParseSlots(Record)
            except ValueError:
                continue
            Written = SlotRecord(
                SlotPrefix(Record),
                tuple(
                    sorted((Token for Token in Tokens if Token is not None))
                    + [None] * sum(1 for Token in Tokens if Token is None)
                ),
            )
        elif Record[:2] == b"\x03\x11":
            Width = (len(Record) - 46) // 2 + 1
            Prefix = 0x80 if Width == 2 else 0
            Written = PairRecord((Label & 0x3F) | Prefix, ((Label + 1) & 0x3F) | Prefix)
            Label += 2
        else:
            continue
        if len(Written) == Finish - Begin:
            Section[Begin:Finish] = Written
    return bytes(Section)


# one record family shares seven byte references that can be relabelled freely
def InstanceValues(SectionBody: bytes) -> list[bytes]:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Values: list[bytes] = []
    for Begin, Finish in zip(Starts, Stops):
        if Finish - Begin not in KInstanceSizes:
            continue
        if SectionBody[Begin + 4 : Begin + 6] != KInstanceFrame:
            continue
        if SectionBody[Begin + 12 : Begin + 14] != KInstanceClass:
            continue
        Position = Begin + KInstanceSkip
        while Position + KReference <= Finish - 3:
            Marker = Position
            while Marker < Finish and SectionBody[Marker] == 0:
                Marker += 1
            if Marker >= Finish or SectionBody[Marker] not in KReferenceTags:
                break
            Values.append(SectionBody[Marker + 1 : Marker + 1 + KReference])
            Position = Marker + 1 + KReference
    return Values


# references are shared so every occurrence takes the same new label
def RelabelRefs(SectionBody: bytes) -> bytes:
    Values = InstanceValues(SectionBody)
    if not Values:
        return SectionBody
    Output = bytes(SectionBody)
    Label = 1
    for Value in dict.fromkeys(Values):
        if len(Value) != KReference:
            continue
        Replacement = bytes([0x40 + (Label & 0x3F), 0x11, 0x22, 0x33, 0x44, 0x55, 0x66])
        if Replacement in Output or Output.count(Value) < 1:
            continue
        Label += 1
        Output = Output.replace(Value, Replacement)
    return Output


# a slot record lists occupied and empty registry slots in hash order
KSlotFrame = bytes.fromhex("02024100364104010111")

# needed so kslot family stays a single named source for the nx adapter
KSlotFamily = b"\x02\x02\x41\x00"

# needed so kslot empty stays a single named source for the nx adapter
KSlotEmpty = 0xFF

# needed so kslot occupied stays a single named source for the nx adapter
KSlotOccupied = 0x80

# needed so kslot label at stays a single named source for the nx adapter
KSlotLabelAt = 0x10


# the slot frame is a class byte and a kind byte inside a fixed run of markers
def SlotPrefix(Record: bytes) -> bytes:
    if (
        Record[:2] == b"\x02\x02"
        and Record[3] == 0
        and Record[4] == 0x36
        and Record[6:10] == b"\x04\x01\x01\x11"
        and len(Record) > 10
    ):
        return Record[:10]
    raise ValueError("NX slot record has no known frame")


# the slot grammar reads back as the same token list it writes
def ParseSlots(Record: bytes) -> tuple[int | None, ...]:
    Prefix = SlotPrefix(Record)
    Tokens: list[int | None] = []
    Position = len(Prefix)
    while Position < len(Record):
        if Record[Position] == KSlotEmpty:
            Tokens.append(None)
            Position += 1
        elif Record[Position] == KSlotOccupied and Position + 1 < len(Record):
            Tokens.append(Record[Position + 1])
            Position += 2
        else:
            raise ValueError("NX slot record token is invalid")
    return tuple(Tokens)


# needed so slot record keeps its nx behaviour in one reviewable place
def SlotRecord(Prefix: bytes, Tokens: tuple[int | None, ...]) -> bytes:
    Output = bytearray(Prefix)
    for Token in Tokens:
        if Token is None:
            Output.append(KSlotEmpty)
        elif 0 <= Token <= 0xFF:
            Output.extend((KSlotOccupied, Token))
        else:
            raise ValueError("NX slot record token is out of range")
    return bytes(Output)


# the 02 02 41 00 family stores two byte tokens and accepts any consistent labels
def RelabelTokens(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Spans = [
        (Begin, Finish)
        for Begin, Finish in zip(Starts, Stops)
        if SectionBody[Begin : Begin + 2] == b"\x02\x02"
        and SectionBody[Begin + 3] == 0
        and SectionBody[Begin + 4] == 0x35
    ]
    if not Spans:
        return SectionBody
    Values: dict[int, int] = {}
    for Begin, Finish in Spans:
        for Position in range(Begin, Finish - 1):
            if SectionBody[Position] == KSlotOccupied:
                Value = SectionBody[Position + 1]
                Values[Value] = KSlotLabelAt + len(Values)
    Output = bytearray(SectionBody)
    for Begin, Finish in Spans:
        for Position in range(Begin, Finish - 1):
            if Output[Position] == KSlotOccupied and Output[Position + 1] in Values:
                Output[Position + 1] = Values[Output[Position + 1]]
    return bytes(Output)


# a lane record names a count then a flag run a mask and a list of slot tokens
KLaneMarker = b"\x02\xe0"

# needed so klane tail stays a single named source for the nx adapter
KLaneTail = b"\x01\x11"

# needed so ktext token stays a single named source for the nx adapter
KTextToken = 0x03


# a text token is a tag a length and the bytes it counts
def LaneTokens(Record: bytes, Start: int) -> tuple[bytes, ...]:
    Tokens: list[bytes] = []
    Position = Start
    while Position < len(Record):
        Marker = Record[Position]
        if Marker == KSlotEmpty:
            Tokens.append(Record[Position : Position + 1])
            Position += 1
        elif Marker == KSlotOccupied and Position + 1 < len(Record):
            Tokens.append(Record[Position : Position + 2])
            Position += 2
        elif Marker == KTextToken and Position + 1 < len(Record):
            Width = Record[Position + 1]
            Tokens.append(Record[Position : Position + 2 + Width])
            Position += 2 + Width
        elif 0x10 <= Marker < KSlotOccupied:
            Tokens.append(Record[Position : Position + 1])
            Position += 1
        else:
            raise ValueError("NX lane record token is invalid")
    return tuple(Tokens)


# needed so lane parts keeps its nx behaviour in one reviewable place
def LaneParts(Record: bytes) -> tuple[int, bytes, bytes, tuple[bytes, ...]]:
    if len(Record) < 12 or Record[1] != 0x11 or Record[4] != 0x11:
        raise ValueError("NX lane record has no known header")
    Count = Record[0]
    if Record[2] != Count:
        raise ValueError("NX lane record count is not repeated")
    MarkerAt = Record.find(KLaneMarker, 5)
    if MarkerAt < 0:
        raise ValueError("NX lane record has no mask marker")
    Flags = Record[5:MarkerAt]
    MaskAt = MarkerAt + len(KLaneMarker)
    if Record[MaskAt + 4 : MaskAt + 6] != KLaneTail:
        raise ValueError("NX lane record mask is not terminated")
    return (Count, Flags, Record[MaskAt : MaskAt + 4], LaneTokens(Record, MaskAt + 6))


# needed so lane record keeps its nx behaviour in one reviewable place
def LaneRecord(
    Count: int, Flags: bytes, MaskValue: bytes, Tokens: tuple[bytes, ...]
) -> bytes:
    if len(MaskValue) != 4:
        raise ValueError("NX lane record mask must be four bytes")
    if not 0 <= Count <= 0xFF:
        raise ValueError("NX lane record count must fit one byte")
    Output = bytearray([Count, 0x11, Count, 0x01, 0x11])
    Output.extend(Flags)
    Output.extend(KLaneMarker)
    Output.extend(MaskValue)
    Output.extend(KLaneTail)
    for Token in Tokens:
        Output.extend(Token)
    return bytes(Output)


# labels are free and shared so one map relabels every lane token consistently
def RelabelLanes(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    LaneRecords: list[tuple[int, int, tuple[bytes, ...]]] = []
    Labels: dict[bytes, int] = {}
    for Begin, Finish in zip(Starts, Stops):
        Record = bytes(SectionBody[Begin:Finish])
        try:
            _, _, _, Tokens = LaneParts(Record)
        except ValueError:
            continue
        LaneRecords.append((Begin, Finish, Tokens))
        for Token in Tokens:
            if Token[0] == KSlotOccupied or 0x10 <= Token[0] < KSlotOccupied:
                if Token not in Labels:
                    Labels[Token] = 0x10 + len(Labels)
    if not LaneRecords:
        return SectionBody
    Section = bytearray(SectionBody)
    for Begin, Finish, Tokens in LaneRecords:
        LaneCount, Flags, MaskValue, _ = LaneParts(bytes(SectionBody[Begin:Finish]))
        Written = [
            (
                bytes([KSlotOccupied, Labels[Token]])
                if Token[0] == KSlotOccupied
                else (
                    bytes([Labels[Token]])
                    if 0x10 <= Token[0] < KSlotOccupied
                    else Token
                )
            )
            for Token in Tokens
        ]
        Built = LaneRecord(LaneCount, Flags, MaskValue, tuple(Written))
        if len(Built) == Finish - Begin:
            Section[Begin:Finish] = Built
    return bytes(Section)


# a named view record carries its name as a length prefixed text token
KViewHead = b"\x02\x02\x41\x41"

# needed so kview heads stays a single named source for the nx adapter
KViewHeads = (
    b"\x02\x02\x41\x41",
    b"\x02\x02\x41\x4b",
    b"\x02\x02\x41\x06",
    b"\x02\x02\x42\x0c",
    b"\x02\x02\x3a\x0c",
    b"\x02\x02\xff\x0c",
    b"\x02\x02\x42\x06",
    b"\x02\x02\x3a\x06",
    b"\x02\x02\xff\x06",
)


# needed so view name keeps its nx behaviour in one reviewable place
def ViewName(Record: bytes) -> tuple[bytes, int, int]:
    if Record[:4] not in KViewHeads:
        raise ValueError("NX view record has no known head")
    for Position in range(len(KViewHead), len(Record) - 2):
        if Record[Position] != KTextToken:
            continue
        Width = Record[Position + 1]
        if Width < 2 or Position + 2 + Width > len(Record):
            continue
        if Record[Position + Width] != 0:
            continue
        Label = Record[Position + 2 : Position + Width]
        if not Label or not all(0x20 <= Sample < 0x7F for Sample in Label):
            continue
        return (Label, Position, Width)
    raise ValueError("NX view record carries no name token")


# the name keeps its room so the record length and pointer stay unchanged
def RenameView(Record: bytes, ViewLabel: bytes) -> bytes:
    _, Position, Width = ViewName(Record)
    if len(ViewLabel) + 2 != Width:
        raise ValueError("NX view name must keep its byte length")
    Output = bytearray(Record)
    Output[Position + 2 : Position + Width] = ViewLabel
    return bytes(Output)


# a numeric word is an expression handle padded to four bytes
def ValueWord(Value: float) -> bytes:
    return EncodeValue(Value).to_bytes(2, "little") + bytes(2)


# needed so read value word keeps its nx behaviour in one reviewable place
def ReadValueWord(WordValue: bytes) -> int:
    if len(WordValue) != 4 or WordValue[2:] != bytes(2):
        raise ValueError("NX value word must be a handle and two zero bytes")
    return int.from_bytes(WordValue[:2], "little")


# a float word is a single precision value widened to a double whose top byte is shifted
KFloatShift = 0x10


# needed so float word keeps its nx behaviour in one reviewable place
def FloatWord(Value: float) -> bytes:
    Single = Struct.unpack(">f", Struct.pack(">f", Value))[0]
    DoubleBytes = Struct.pack(">d", Single)
    return bytes([(DoubleBytes[0] - KFloatShift) & 0xFF]) + DoubleBytes[1:]


# needed so read float word keeps its nx behaviour in one reviewable place
def ReadFloatWord(WordValue: bytes) -> float:
    if not 1 <= len(WordValue) <= 8:
        raise ValueError("NX float word must be one to eight bytes")
    Shifted = bytes([(WordValue[0] + KFloatShift) & 0xFF]) + WordValue[1:].ljust(
        7, bytes(1)
    )
    Value: float = Struct.unpack(">d", Shifted)[0]
    return Value


# token family words are rewritten from decoded values
KWordTags = (0x30, 0xB0, 0x2F, 0x4F, 0xCF, 0x5F, 0xDF, 0xAF)


# needed so rewrite word run keeps its nx behaviour in one reviewable place
def RewriteWordRun(Record: bytes, Begin: int, Finish: int) -> bytes:
    Output = bytearray(Record)
    Position = Begin
    while Position < Finish:
        if Record[Position] == 0x50 and Record[Position + 3] == 0:
            Handle = ReadValueWord(Record[Position : Position + 4])
            Output[Position : Position + 4] = Handle.to_bytes(2, "little") + bytes(2)
            Position += 4
            continue
        if Record[Position] in KWordTags and Position + 8 <= Finish:
            WordBytes = Record[Position : Position + 8]
            try:
                Number = ReadFloatWord(WordBytes)
            except (ValueError, Struct.error):
                Position += 1
                continue
            try:
                Written = FloatWord(Number)
            except (OverflowError, ValueError):
                Position += 1
                continue
            if Written == WordBytes:
                Output[Position : Position + 8] = Written
                Position += 8
                continue
        Position += 1
    return bytes(Output)


# display values in every record family are rewritten from numbers
def RewriteValues(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Section = bytearray(SectionBody)
    for Begin, Finish in zip(Starts, Stops):
        Record = bytes(SectionBody[Begin:Finish])
        if Record[:2] != b"\x02\x02":
            continue
        Written = RewriteWordRun(Record, 14, len(Record))
        if len(Written) == Finish - Begin:
            Section[Begin:Finish] = Written
    return bytes(Section)


# the small 5f records are a fixed frame a zero run and a free flag
KSmallFrame = bytes.fromhex("0202ff005f010401")


# needed so small record keeps its nx behaviour in one reviewable place
def SmallRecord(Length: int, TailFlag: int = 1) -> bytes:
    if Length < len(KSmallFrame) + 2:
        raise ValueError("NX small record must carry a zero run and a flag")
    if not 0 <= TailFlag <= 0xFF:
        raise ValueError("NX small record flag must fit one byte")
    return KSmallFrame + bytes(Length - len(KSmallFrame) - 1) + bytes([TailFlag])


# needed so read small record keeps its nx behaviour in one reviewable place
def ReadSmallRecord(Record: bytes) -> tuple[int, int]:
    if not Record.startswith(KSmallFrame):
        raise ValueError("NX small record has no known frame")
    if len(Record) < len(KSmallFrame) + 2:
        raise ValueError("NX small record is too short")
    if Record[len(KSmallFrame) : -1] != bytes(len(Record) - len(KSmallFrame) - 1):
        raise ValueError("NX small record payload is not a zero run")
    return (len(Record), Record[-1])


# the nesting member of the small family is a run of heads and leaves
KNestEnd = b"\x02\x02"

# needed so knest head stays a single named source for the nx adapter
KNestHead = 0x03


# needed so read nesting keeps its nx behaviour in one reviewable place
def ReadNesting(Record: bytes) -> tuple[tuple[int, int], ...]:
    if not Record.startswith(KSmallFrame) or not Record.endswith(KNestEnd):
        raise ValueError("NX nesting record has no known frame")
    Segments: list[tuple[int, int]] = []
    Position = len(KSmallFrame)
    while Position < len(Record) - len(KNestEnd):
        SegmentHead = Record[Position]
        Leaves = 0
        Position += 1
        while Position < len(Record) and Record[Position] == 1:
            Leaves += 1
            Position += 1
        Segments.append((SegmentHead, Leaves))
    return tuple(Segments)


# needed so nesting record keeps its nx behaviour in one reviewable place
def NestingRecord(Segments: tuple[tuple[int, int], ...]) -> bytes:
    Output = bytearray(KSmallFrame)
    for SegmentHead, Leaves in Segments:
        if not 0 <= SegmentHead <= 0xFF or Leaves < 1:
            raise ValueError("NX nesting segment is out of range")
        Output.append(SegmentHead)
        Output.extend(bytes([1]) * Leaves)
    Output.extend(KNestEnd)
    return bytes(Output)


# the nesting record is unvalidated so its heads are rewritten to the leaf form
def RewriteNesting(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Section = bytearray(SectionBody)
    for Begin, Finish in zip(Starts, Stops):
        Record = bytes(SectionBody[Begin:Finish])
        try:
            Segments = ReadNesting(Record)
        except ValueError:
            continue
        Canonical = NestingRecord(tuple((KNestHead, Leaves) for _, Leaves in Segments))
        if len(Canonical) == Finish - Begin:
            Section[Begin:Finish] = Canonical
    return bytes(Section)


# the small mark record carries one marker byte and a free terminator
KMarkFrame = bytes.fromhex("0202410038 0103 02".replace(" ", ""))

# needed so kmark value stays a single named source for the nx adapter
KMarkValue = 0x82


# needed so mark record keeps its nx behaviour in one reviewable place
def MarkRecord(Record: bytes) -> bytes:
    if len(Record) != 14 or Record[:8] != KMarkFrame:
        raise ValueError("NX mark record has no known frame")
    Payload = bytearray(Record[8:13])
    if Payload.count(0x81) != 1:
        raise ValueError("NX mark record does not carry one marker")
    Payload[Payload.index(0x81)] = KMarkValue
    return KMarkFrame + bytes(Payload) + b"\x01"


# the marker and terminator are unvalidated so the writer normalises both
def RewriteMarks(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Section = bytearray(SectionBody)
    for Begin, Finish in zip(Starts, Stops):
        Record = bytes(SectionBody[Begin:Finish])
        try:
            Written = MarkRecord(Record)
        except ValueError:
            continue
        if len(Written) == Finish - Begin:
            Section[Begin:Finish] = Written
    return bytes(Section)


# three small families carry a free label byte and a validated id byte
KLabelFrame = bytes.fromhex("47040401c044040080810209")

# needed so klabel value stays a single named source for the nx adapter
KLabelValue = 0


# needed so label record keeps its nx behaviour in one reviewable place
def LabelRecord(Record: bytes, Blocks: int, Block: int, Index: int) -> bytes:
    if (
        len(Record) != 21
        or Record[:2] != b"\x02\x02"
        or Record[3] != 0
        or Record[4:16] != KLabelFrame
    ):
        raise ValueError("NX label record has no known frame")
    Carry = CarryId(Blocks, Block, Index)
    return Record[:16] + bytes([KLabelValue]) + Record[17:20] + bytes([Carry])


# the label byte is free and sits before a validated id so only it is rewritten
def RewriteLabels(SectionBody: bytes) -> bytes:
    Count = ObjectCount(SectionBody)
    TableAt = TableStart(SectionBody, Count)
    Starts = [
        int(Struct.unpack_from("<I", SectionBody, TableAt + 4 * Index)[0])
        for Index in range(Count)
    ]
    Stops = Starts[1:] + [len(SectionBody) - 12]
    Positions = [
        Index
        for Index, (Begin, Finish) in enumerate(zip(Starts, Stops))
        if SectionBody[Begin:Finish][:2] == b"\x02\x02"
        and SectionBody[Begin + 3] == 0
        and SectionBody[Begin + 4 : Begin + 16] == KLabelFrame
    ]
    if not Positions or len(Positions) % 12:
        return SectionBody
    Blocks = len(Positions) // 12
    Section = bytearray(SectionBody)
    for Ordinal, Index in enumerate(Positions):
        Begin, Finish = Starts[Index], Stops[Index]
        Written = LabelRecord(
            bytes(SectionBody[Begin:Finish]), Blocks, Ordinal // 12, Index
        )
        if len(Written) == Finish - Begin:
            Section[Begin:Finish] = Written
    return bytes(Section)


# the carry id descends per block and shifts with the block count and ordinal
def CarryId(Blocks: int, Block: int, Index: int) -> int:
    if Blocks < 1 or not 0 <= Block < Blocks:
        raise ValueError("NX carry id needs a block inside the block count")
    Value = 70 + 6 * Blocks + Block - Index
    if not 0 <= Value <= 0xFF:
        raise ValueError("NX carry id must fit one byte")
    return Value
