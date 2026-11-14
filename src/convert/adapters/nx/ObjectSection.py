from __future__ import annotations as Annotations

import struct as Struct

from convert.adapters.nx.ExprValue import EncodeValue

# the root object section is lanes then a table then an order array then records
KSlice = 0x30C
KOrderStart = 0x664
KGapStart = 0x9B8
KRecordCount = 214
KInstanceSizes = (27, 34, 48)
KReferenceTags = (0x30, 0xB0)
KInstanceFrame = b"\x00\xf0"
KInstanceClass = b"\xc0\x45"
KReference = 7
KInstanceSkip = 21
KNames = b"\x77\x0fm_nextInstance"
KHeadTag = b"\x41\x00\x03\x03"
KAnchor = b"\xe0\x6a\xf8"
KUnset = b"\xff" * 7
KHeadPrefix = bytes.fromhex("0305020004050100")
KHeadSuffix = bytes.fromhex("80d5021304050100010180d5021380d6020000")
KHeadReserve = 43


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
def ReplaceHead(
    SectionBody: bytes, PartText: bytes, Identity: bytes | None = None
) -> bytes:
    TableAt, Starts, Records = RecordsOf(SectionBody)
    Source = Records[0]
    AnchorAt = Source.find(KAnchor)
    if AnchorAt < 0:
        raise ValueError("NX root head record carries no anchor")
    Saved = Identity if Identity is not None else Source[AnchorAt + 3 : AnchorAt + 10]
    Emitted = HeadRecord(FitText(PartText, len(Source) - KHeadReserve), Saved)
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


__all__ = [
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
KPairGap = bytes([0xFF]) * 6
KPairTail = bytes([0xFF]) * 8


# registry tokens store up to 0x7f directly and larger values behind a 0x80 prefix
def RegToken(Value: int) -> bytes:
    if not 0 <= Value <= 0x7FFF:
        raise ValueError("NX registry token is out of range")
    if Value <= 0x7F:
        return bytes([Value])
    return bytes([0x80 | (Value >> 8), Value & 0xFF])


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
KSlotFamily = b"\x02\x02\x41\x00"
KSlotEmpty = 0xFF
KSlotOccupied = 0x80
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
KLaneTail = b"\x01\x11"
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


def ViewName(Record: bytes) -> tuple[bytes, int, int]:
    if not Record.startswith(KViewHead):
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


def ReadValueWord(WordValue: bytes) -> int:
    if len(WordValue) != 4 or WordValue[2:] != bytes(2):
        raise ValueError("NX value word must be a handle and two zero bytes")
    return int.from_bytes(WordValue[:2], "little")


# a float word is a single precision value widened to a double whose top byte is shifted
KFloatShift = 0x10


def FloatWord(Value: float) -> bytes:
    Single = Struct.unpack(">f", Struct.pack(">f", Value))[0]
    DoubleBytes = Struct.pack(">d", Single)
    return bytes([(DoubleBytes[0] - KFloatShift) & 0xFF]) + DoubleBytes[1:]


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
            Written = FloatWord(Number)
            if Written == WordBytes:
                Output[Position : Position + 8] = Written
                Position += 8
                continue
        Position += 1
    return bytes(Output)


# display values are rewritten from numbers
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
        if Record[:2] != b"\x02\x02" or Record[4:5] != b"5":
            continue
        Written = RewriteWordRun(Record, 14, len(Record))
        if len(Written) == Finish - Begin:
            Section[Begin:Finish] = Written
    return bytes(Section)
