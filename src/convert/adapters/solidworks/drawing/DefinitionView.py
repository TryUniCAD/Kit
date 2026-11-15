from __future__ import annotations

from dataclasses import dataclass, replace as ReplaceData
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.core.Native import ReadSerialized, Serialized

# the view block holds ten fixed slots
KViewSlots = 10

# the view record payload is a fixed width
KViewPayload = 124

# the view block ends with a fixed tail
KViewTail = 23

# the view record carries a one byte prefix before the first vector
KViewPrefix = 1

# the view record carries two three double vectors
KViewVector = 3

# the view record carries two scale doubles
KViewScale = 1

# the view record carries a two byte gap after the first vector
KViewGapOne = 2

# the view record carries a three byte gap after the second scale
KViewGapTwo = 3

# the view record carries a four byte zero before the index
KViewZero = 4

# the view record carries a three byte gap after the index
KViewGapThree = 3

# the view record carries four reserved doubles
KViewReserved = 4


# callers need the view name and its decoded fields as one value
@dataclass(frozen=True, slots=True)
class ViewRecord:
    NameValue: str
    Prefix: int
    Origin: tuple[float, ...]
    ScaleOne: float
    Normal: tuple[float, ...]
    GapOne: bytes
    ScaleTwo: float
    GapTwo: bytes
    FlagValue: int
    Value: float
    ZeroValue: int
    Index: int
    GapThree: bytes
    Reserved: tuple[float, ...]
    ClassRef: int


# the first half of the payload keeps the prefix vectors and scales together
@dataclass(frozen=True, slots=True)
class ViewHead:
    Prefix: int
    Origin: tuple[float, ...]
    ScaleOne: float
    Normal: tuple[float, ...]
    GapOne: bytes
    ScaleTwo: float
    GapTwo: bytes


# the second half of the payload keeps the flags index and class reference together
@dataclass(frozen=True, slots=True)
class ViewTail:
    FlagValue: int
    Value: float
    ZeroValue: int
    Index: int
    GapThree: bytes
    Reserved: tuple[float, ...]
    ClassRef: int


# the first half is read separately so the payload stays under the split limit
def ViewHeadAt(DataValue: bytes, Offset: int) -> tuple[ViewHead, int]:
    Prefix = DataValue[Offset]
    Offset += KViewPrefix
    Origin = Struct.unpack_from(f"<{KViewVector}d", DataValue, Offset)
    Offset += KViewVector * 8
    (ScaleOne,) = Struct.unpack_from("<d", DataValue, Offset)
    Offset += KViewScale * 8
    Normal = Struct.unpack_from(f"<{KViewVector}d", DataValue, Offset)
    Offset += KViewVector * 8
    GapOne = DataValue[Offset : Offset + KViewGapOne]
    Offset += KViewGapOne
    (ScaleTwo,) = Struct.unpack_from("<d", DataValue, Offset)
    Offset += KViewScale * 8
    GapTwo = DataValue[Offset : Offset + KViewGapTwo]
    Offset += KViewGapTwo
    return ViewHead(Prefix, Origin, ScaleOne, Normal, GapOne, ScaleTwo, GapTwo), Offset


# the second half is read separately so the payload stays under the split limit
def ViewTailAt(DataValue: bytes, Offset: int) -> tuple[ViewTail, int]:
    (FlagValue,) = Struct.unpack_from("<i", DataValue, Offset)
    Offset += 4
    (Value,) = Struct.unpack_from("<d", DataValue, Offset)
    Offset += 8
    (ZeroValue,) = Struct.unpack_from("<i", DataValue, Offset)
    Offset += KViewZero
    Index = DataValue[Offset]
    Offset += 1
    GapThree = DataValue[Offset : Offset + KViewGapThree]
    Offset += KViewGapThree
    Reserved = Struct.unpack_from(f"<{KViewReserved}d", DataValue, Offset)
    Offset += KViewReserved * 8
    (ClassRef,) = Struct.unpack_from("<H", DataValue, Offset)
    Offset += 2
    return (
        ViewTail(FlagValue, Value, ZeroValue, Index, GapThree, Reserved, ClassRef),
        Offset,
    )


# the payload width must match so a shifted record cannot be accepted
def ViewPayloadAt(DataValue: bytes, Offset: int) -> tuple[ViewRecord, int]:
    Start = Offset
    HeadValue, Offset = ViewHeadAt(DataValue, Offset)
    TailValue, Offset = ViewTailAt(DataValue, Offset)
    if Offset - Start != KViewPayload:
        raise SldprtFormatError("drawing view record width is invalid")
    return (
        ViewRecord(
            "",
            HeadValue.Prefix,
            HeadValue.Origin,
            HeadValue.ScaleOne,
            HeadValue.Normal,
            HeadValue.GapOne,
            HeadValue.ScaleTwo,
            HeadValue.GapTwo,
            TailValue.FlagValue,
            TailValue.Value,
            TailValue.ZeroValue,
            TailValue.Index,
            TailValue.GapThree,
            TailValue.Reserved,
            TailValue.ClassRef,
        ),
        Offset,
    )


# the name is read first so the payload can be decoded without it
def ViewRecordAt(DataValue: bytes, Offset: int) -> tuple[ViewRecord, int]:
    NameValue, Offset = ReadSerialized(DataValue, Offset)
    if Offset + KViewPayload > len(DataValue):
        raise SldprtFormatError("drawing view record is truncated")
    Payload, Offset = ViewPayloadAt(DataValue, Offset)
    return ReplaceData(Payload, NameValue=NameValue), Offset


# the block is ten records plus a tail so a short block cannot be accepted
def ViewBlock(DataValue: bytes) -> tuple[tuple[ViewRecord, ...], bytes]:
    Records: list[ViewRecord] = []
    Offset = 0
    SlotIndex = 0
    while SlotIndex < KViewSlots:
        Record, Offset = ViewRecordAt(DataValue, Offset)
        Records.append(Record)
        SlotIndex += 1
    TailValue = DataValue[Offset:]
    if len(TailValue) != KViewTail:
        raise SldprtFormatError("drawing view block tail is invalid")
    return tuple(Records), TailValue


# the writer needs the exact field order and gaps to stay valid
def EncodeViewBlock(Records: tuple[ViewRecord, ...], TailValue: bytes) -> bytes:
    Output = bytearray()
    for Record in Records:
        Output.extend(Serialized(Record.NameValue))
        Output.extend(bytes((Record.Prefix,)))
        Output.extend(Struct.pack(f"<{KViewVector}d", *Record.Origin))
        Output.extend(Struct.pack("<d", Record.ScaleOne))
        Output.extend(Struct.pack(f"<{KViewVector}d", *Record.Normal))
        Output.extend(Record.GapOne)
        Output.extend(Struct.pack("<d", Record.ScaleTwo))
        Output.extend(Record.GapTwo)
        Output.extend(Struct.pack("<i", Record.FlagValue))
        Output.extend(Struct.pack("<d", Record.Value))
        Output.extend(Struct.pack("<i", Record.ZeroValue))
        Output.extend(bytes((Record.Index,)))
        Output.extend(Record.GapThree)
        Output.extend(Struct.pack(f"<{KViewReserved}d", *Record.Reserved))
        Output.extend(Struct.pack("<H", Record.ClassRef))
    Output.extend(TailValue)
    return bytes(Output)
