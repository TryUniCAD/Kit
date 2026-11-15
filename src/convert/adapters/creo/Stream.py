from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from dataclasses import field as MakeField

# three scalars are stored as single bytes because they dominate
KOneByteDouble = {0x0F: 0.0, 0x10: 1.0, 0x18: 1.0}

# field names are ascii so the scanner can reject noise early
KNameBytes = frozenset(
    b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_()[] .:-+"
)

# a runaway name would mean we lost stream alignment
KMaxFieldName = 60

# absurd array counts mean corruption so they are capped
KMaxArrayCount = 65536


# names and types travel together because callers need both
@dataclass
class StreamField:
    name: str
    type_id: int
    count: int | None = None
    offset: int = 0


# the decoded tree is what every consumer queries by name
@dataclass
class StreamNode:
    name: str
    type_id: int
    value: object = None
    offset: int = 0
    children: list["StreamNode"] = MakeField(default_factory=list)


# dimensions are the only parametric value our readers expose
@dataclass(frozen=True, slots=True)
class CreoDimension:
    value: float
    reference: int | None
    offset: int
    length: int


# compact integers appear in every section so one decoder serves all
def ReadCompactAt(DataValue: bytes, Position: int) -> tuple[int | None, int]:
    if Position >= len(DataValue):
        return None, Position
    FirstValue = DataValue[Position]
    if FirstValue <= 0x7F:
        return FirstValue, Position + 1
    if FirstValue <= 0xBF:
        if Position + 1 >= len(DataValue):
            return None, Position
        return ((FirstValue & 0x3F) << 8) | DataValue[Position + 1], Position + 2
    if FirstValue <= 0xDF:
        if Position + 2 >= len(DataValue):
            return None, Position
        return (
            ((FirstValue & 0x1F) << 16)
            | (DataValue[Position + 1] << 8)
            | DataValue[Position + 2],
            Position + 3,
        )
    if FirstValue == 0xF6:
        return -1, Position + 1
    if FirstValue == 0xE7:
        if Position + 1 >= len(DataValue):
            return None, Position
        return DataValue[Position + 1], Position + 2
    if 0xE8 <= FirstValue <= 0xEB:
        Width = FirstValue - 0xE7
        if Position + Width >= len(DataValue):
            return None, Position
        return (
            int.from_bytes(DataValue[Position + 1 : Position + 1 + Width], "big"),
            Position + 1 + Width,
        )
    return None, Position


# array counts can be implicit so peeking avoids consuming them
def PeekCount(DataValue: bytes, Position: int) -> int | None:
    if Position >= len(DataValue):
        return None
    TokenValue = DataValue[Position]
    if TokenValue == 0xF8:
        CountValue, _AfterValue = ReadCompactAt(DataValue, Position + 1)
        return CountValue
    if TokenValue == 0xF9:
        RowsValue, NextValue = ReadCompactAt(DataValue, Position + 1)
        ColsValue, _AfterValue = ReadCompactAt(DataValue, NextValue)
        if RowsValue is None or ColsValue is None:
            return None
        return RowsValue * ColsValue
    return None


# a cheap field index keeps later lookups from rescanning
def ScanFields(DataValue: bytes) -> list[StreamField]:
    Fields: list[StreamField] = []
    Position = 0
    while Position < len(DataValue) - 2:
        if DataValue[Position] == 0xE0:
            TypeValue = DataValue[Position + 1]
            EndValue = DataValue.find(b"\x00", Position + 2)
            if 0 < EndValue and EndValue - Position < KMaxFieldName:
                NameValue = DataValue[Position + 2 : EndValue]
                if NameValue and all(Value in KNameBytes for Value in NameValue):
                    Fields.append(
                        StreamField(
                            NameValue.decode("latin-1"),
                            TypeValue,
                            PeekCount(DataValue, EndValue + 1),
                            Position,
                        )
                    )
                    Position = EndValue + 1
                    continue
        Position += 1
    return Fields


# byte level cursor keeps parsing state in one place
class StreamReader:

    # the reader never copies so large sections stay cheap
    def __init__(self, DataValue: bytes) -> None:
        self.DataValue = DataValue
        self.Position = 0

    # every token read funnels here so bounds checks happen once
    def Byte(self) -> int:
        Value = self.DataValue[self.Position]
        self.Position += 1
        return Value

    # fixed spans are needed for doubles and names
    def Take(self, Count: int) -> bytes:
        Value = self.DataValue[self.Position : self.Position + Count]
        self.Position += Count
        return Value

    # names are nul terminated and appear everywhere
    def CString(self) -> str:
        EndValue = self.DataValue.find(b"\x00", self.Position)
        if EndValue < 0:
            EndValue = len(self.DataValue)
        Value = self.DataValue[self.Position : EndValue].decode("latin-1")
        self.Position = EndValue + 1
        return Value

    # compact widths are the most error prone part of the grammar
    def CompactInt(self) -> int | None:
        NegateValue = False
        if (
            self.Position < len(self.DataValue)
            and self.DataValue[self.Position] == 0xF5
        ):
            NegateValue = True
            self.Position += 1
        Value, NextPosition = ReadCompactAt(self.DataValue, self.Position)
        if Value is None:
            return None
        self.Position = NextPosition
        return -Value if NegateValue else Value


# nested records need a parser distinct from the cursor
class StreamParser:

    # the schema table is shared across nested records
    def __init__(
        self, DataValue: bytes, Boundaries: dict[int, int] | None = None
    ) -> None:
        self.Reader = StreamReader(DataValue)
        self.Nodes: list[StreamNode] = []
        self.Boundaries = Boundaries or {}
        self.Fields = ScanFields(DataValue)
        self.ByOffset = {Field.offset: Index for Index, Field in enumerate(self.Fields)}
        self.Index = 0
        self.FeatureStart = 0
        self.StructureStart: list[int] = []

    # doubles come in several lanes and one owner decodes them all
    def ReadDouble(self) -> float | None:
        Reader = self.Reader
        if Reader.Position >= len(Reader.DataValue):
            return None
        FirstValue = Reader.DataValue[Reader.Position]
        if FirstValue in KOneByteDouble:
            Reader.Position += 1
            return KOneByteDouble[FirstValue]
        if FirstValue in (0x46, 0x2D):
            Reader.Position += 1
            LeadValue = b"\x40" if FirstValue == 0x46 else b"\xc0"
            return struct.unpack(">d", LeadValue + Reader.Take(7))[0]
        if FirstValue in (0xD5, 0x4F):
            Reader.Position += 1
            LeadValue = b"\xbf" if FirstValue == 0xD5 else b"\x3f"
            return struct.unpack(">d", LeadValue + Reader.Take(6) + b"\x00")[0]
        if FirstValue == 0x52:
            Reader.Position += 1
            return struct.unpack(">d", Reader.Take(8))[0]
        if FirstValue == 0x2F:
            TailValue = Reader.DataValue[Reader.Position + 1 : Reader.Position + 9]
            StopValue = TailValue.find(b"\x00")
            TextTail = TailValue[:StopValue] if StopValue >= 0 else b""
            if TextTail and all(
                ByteValue in b"0123456789+-." for ByteValue in TextTail
            ):
                Reader.Position += 1
                TextValue = Reader.DataValue[
                    Reader.Position : Reader.Position + len(TextTail)
                ].decode("latin-1")
                Reader.Position += len(TextTail) + 1
                return float(TextValue)
        StartValue = Reader.Position
        while (
            Reader.Position < len(Reader.DataValue)
            and chr(Reader.DataValue[Reader.Position]) in "0123456789abcdefABCDEF"
        ):
            Reader.Position += 1
        if Reader.Position == StartValue:
            Reader.Position += 8
            return None
        TextValue = Reader.DataValue[StartValue : Reader.Position].decode("latin-1")
        if len(TextValue) % 2:
            TextValue = "0" + TextValue
        RawValue = bytes.fromhex(TextValue)[:8].ljust(8, b"\x00")
        return struct.unpack(">d", RawValue)[0]

    # scalars and arrays dispatch on the same declared type
    def ReadScalar(self, TypeValue: int) -> object:
        if TypeValue in (0x01, 0x05, 0x07, 0x08, 0x09, 0x0B):
            return self.Reader.CompactInt()
        if TypeValue == 0x02:
            return self.ReadDouble()
        if TypeValue in (0x03, 0x0A):
            return self.Reader.CString()
        if TypeValue == 0x04:
            return self.Reader.Byte()
        if TypeValue == 0x06:
            return struct.unpack(">f", self.Reader.Take(4))[0]
        return None

    # arrays are where repeat tokens and counts interact
    def ReadArray(self, TypeValue: int, Count: int | None) -> list[object]:
        Reader = self.Reader
        Values: list[object] = []
        if Count is not None and Count > KMaxArrayCount:
            Count = KMaxArrayCount
        while Reader.Position < len(Reader.DataValue):
            if Count is not None and len(Values) >= Count:
                if Reader.DataValue[Reader.Position] == 0xFB:
                    Reader.Position += 1
                break
            TokenValue = Reader.DataValue[Reader.Position]
            if TokenValue == 0xE7:
                Reader.Position += 1
                RepeatValue = Reader.CompactInt()
                if Values and RepeatValue and RepeatValue <= KMaxArrayCount:
                    Values.extend([Values[-1]] * RepeatValue)
                continue
            if 0xE4 <= TokenValue <= 0xE6:
                Reader.Position += 1
                if Values:
                    Values.extend([Values[-1]] * (TokenValue - 0xE3))
                continue
            if TokenValue == 0xF7:
                Reader.Position += 1
                Values.append(Reader.CompactInt())
                continue
            if TokenValue == 0xFB:
                Reader.Position += 1
                break
            if TokenValue in (0xE0, 0xE1, 0xE2, 0xE3) or 0xF1 <= TokenValue <= 0xF4:
                break
            BeforeValue = Reader.Position
            Values.append(self.ReadScalar(TypeValue))
            if Reader.Position == BeforeValue:
                break
        return Values

    # values may be scalar array or record so dispatch lives here
    def ReadValue(self, TypeValue: int, Count: int | None) -> object:
        Reader = self.Reader
        if Reader.Position >= len(Reader.DataValue):
            return None
        TokenValue = Reader.DataValue[Reader.Position]
        if TokenValue in (0xFB, 0xF0):
            Reader.Position += 1
            return None
        if TokenValue == 0xE1:
            Reader.Position += 1
            return None
        if TokenValue in (0xE2, 0xE3):
            Reader.Position += 1
            self.StructureStart.append(self.Index)
            return StreamNode("<compound>", TokenValue)
        if TokenValue in (0xF8, 0xF9):
            Reader.Position += 1
            if TokenValue == 0xF8:
                NewCount = Reader.CompactInt()
            else:
                RowsValue = Reader.CompactInt()
                ColsValue = Reader.CompactInt()
                NewCount = (RowsValue or 0) * (ColsValue or 0)
            return self.ReadArray(TypeValue, NewCount)
        if TypeValue == 0x00:
            return Reader.CompactInt()
        return self.ReadScalar(TypeValue)

    # each field binds a name to a decoded value
    def ReadField(self, Field: StreamField) -> StreamNode:
        Reader = self.Reader
        StartValue = Reader.Position
        while (
            Reader.Position < len(Reader.DataValue)
            and 0xF1 <= Reader.DataValue[Reader.Position] <= 0xF4
        ):
            CloseValue = Reader.DataValue[Reader.Position] - 0xF0
            Reader.Position += 1
            for _ in range(CloseValue):
                if self.StructureStart:
                    self.StructureStart.pop()
        TokenValue = (
            Reader.DataValue[Reader.Position]
            if Reader.Position < len(Reader.DataValue)
            else None
        )
        if TokenValue is not None and 0xE4 <= TokenValue <= 0xE6:
            Reader.Position += 1
            Node = StreamNode(Field.name, Field.type_id, offset=StartValue)
        elif (
            Field.count is not None
            and Field.type_id != 0x00
            and TokenValue not in (0xF8, 0xF9)
        ):
            Node = StreamNode(
                Field.name,
                Field.type_id,
                self.ReadArray(Field.type_id, Field.count),
                StartValue,
            )
        else:
            Node = StreamNode(
                Field.name,
                Field.type_id,
                self.ReadValue(Field.type_id, Field.count),
                StartValue,
            )
            if isinstance(Node.value, list) and Field.type_id != 0x00:
                Field.count = len(Node.value)
        self.Nodes.append(Node)
        return Node

    # callers want the whole tree without managing nesting
    def Run(self) -> list[StreamNode]:
        Reader = self.Reader
        Iterations = 0
        LimitValue = len(Reader.DataValue) * 16 + 1024
        while Reader.Position < len(Reader.DataValue):
            Iterations += 1
            if Iterations > LimitValue:
                break
            TokenValue = Reader.DataValue[Reader.Position]
            if TokenValue == 0xE0:
                StartValue = Reader.Position
                Reader.Position += 1
                TypeValue = Reader.Byte()
                NameValue = Reader.CString()
                KnownIndex = self.ByOffset.get(StartValue)
                if KnownIndex is not None:
                    Field = self.Fields[KnownIndex]
                else:
                    Field = StreamField(NameValue, TypeValue, offset=StartValue)
                    self.ByOffset[StartValue] = len(self.Fields)
                    self.Fields.append(Field)
                    KnownIndex = len(self.Fields) - 1
                self.Index = KnownIndex
                if NameValue == "first_feat_ptr":
                    self.FeatureStart = KnownIndex + 1
                Node = self.ReadField(Field)
                self.Index += 1
                if NameValue == "next_feat_ptr" and isinstance(Node.value, StreamNode):
                    self.Index = self.FeatureStart
                continue
            if 0xF1 <= TokenValue <= 0xF4:
                Reader.Position += 1
                for _ in range(TokenValue - 0xF0):
                    if self.StructureStart:
                        self.StructureStart.pop()
                continue
            if TokenValue == 0xF7:
                Reader.Position += 1
                ReferenceValue = Reader.CompactInt()
                if ReferenceValue is not None and 1 <= ReferenceValue <= len(
                    self.Fields
                ):
                    self.Index = ReferenceValue - 1
                    Field = self.Fields[self.Index]
                    Node = self.ReadField(Field)
                    self.Index += 1
                    if Field.name == "next_feat_ptr" and isinstance(
                        Node.value, StreamNode
                    ):
                        self.Index = self.FeatureStart
                continue
            if self.Index >= len(self.Fields) and self.StructureStart:
                self.Index = self.StructureStart[-1]
            if self.Index < len(self.Fields):
                if TokenValue == 0xE3 and Reader.Position in self.Boundaries:
                    Reader.Position += 1
                    self.Index = self.Boundaries[Reader.Position - 1]
                Field = self.Fields[self.Index]
                Node = self.ReadField(Field)
                self.Index += 1
                if Field.name == "next_feat_ptr" and isinstance(Node.value, StreamNode):
                    self.Index = self.FeatureStart
                continue
            if TokenValue in (0xE2, 0xE3):
                Reader.Position += 1
                self.Nodes.append(StreamNode("<compound>", TokenValue))
                continue
            if TokenValue == 0xE1:
                Reader.Position += 1
                continue
            Reader.Position += 1
        return self.Nodes


# dimensions are read directly because callers only need values
def ReadDimensions(DataValue: bytes) -> tuple[CreoDimension, ...]:
    Parser = StreamParser(DataValue)
    _ = Parser.Run()
    Dimensions: list[CreoDimension] = []
    for IndexValue, Node in enumerate(Parser.Nodes):
        if Node.name != "value" or not isinstance(Node.value, float):
            continue
        if not math.isfinite(Node.value):
            continue
        ReferenceValue: int | None = None
        for NextNode in Parser.Nodes[IndexValue + 1 : IndexValue + 8]:
            if NextNode.name == "dim_ref":
                if isinstance(NextNode.value, int):
                    ReferenceValue = NextNode.value
                elif isinstance(NextNode.value, list) and NextNode.value:
                    CandidateValue = NextNode.value[0]
                    if isinstance(CandidateValue, int):
                        ReferenceValue = CandidateValue
                break
        Dimensions.append(CreoDimension(Node.value, ReferenceValue, Node.offset, 8))
    return tuple(Dimensions)
