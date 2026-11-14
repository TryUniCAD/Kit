from __future__ import annotations

from dataclasses import dataclass
import struct

# this binding exists because shared behavior needs one stable value
KDelimiter = b"\x10\x24\x04\xff\xff\x00\x00\x00"

# this binding exists because shared behavior needs one stable value
KTrimKinds = frozenset(range(0x40, 0x50))


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class TrimRec:
    kind: int
    offset: int
    counts: tuple[int, int, int]
    total: int
    vector: tuple[float, float, float] | None
    lengths: tuple[int, ...]
    handles: tuple[int, ...]


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class EdgeRec:
    arity: int
    handles: tuple[int, ...]
    offset: int


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class VertRec:
    point: tuple[float, float, float]
    offset: int


# this definition exists because focused behavior needs one stable owner
def Count(SourceData: bytes, Offset: int) -> tuple[int, int]:
    Value = SourceData[Offset]
    if Value != 0xFF:
        return Value, Offset + 1
    return struct.unpack_from("<I", SourceData, Offset + 1)[0], Offset + 5


# this definition exists because focused behavior needs one stable owner
def FindFbb(SourceData: bytes) -> tuple[int, int]:
    BestOffset = -1
    BestCount = 0
    Offset = 0
    Limit = len(SourceData) - 4
    while Offset <= Limit:
        if SourceData[Offset : Offset + 4] not in (
            b"\x30\x04\x04\xff",
            b"\xb0\x04\x04\xff",
        ):
            Offset += 1
            continue
        Start = Offset
        CountValue = 0
        while Offset <= Limit and SourceData[Offset : Offset + 4] in (
            b"\x30\x04\x04\xff",
            b"\xb0\x04\x04\xff",
        ):
            CountValue += 1
            Offset += 8
        if CountValue > BestCount:
            BestOffset = Start
            BestCount = CountValue
    if BestOffset < 0:
        raise ValueError("FBB spine is missing")
    return BestOffset, BestCount


# this definition exists because focused behavior needs one stable owner
def ReadHandles(
    SourceData: bytes, Cursor: int, Total: int, Width: int
) -> tuple[tuple[int, ...], int]:
    Handles: list[int] = []
    for _ in range(Total):
        Handles.append(int.from_bytes(SourceData[Cursor : Cursor + Width], "big"))
        Cursor += Width
    return tuple(Handles), Cursor


# this definition exists because focused behavior needs one stable owner
def ParseTrim(SourceData: bytes, Offset: int, Width: int) -> tuple[TrimRec, int]:
    if SourceData[Offset] != 0x01 or SourceData[Offset + 1] not in KTrimKinds:
        raise ValueError("trim marker is missing")
    KindValue = SourceData[Offset + 1]
    Cursor = Offset + 2
    Counts = [0, 0, 0]
    for Index, MaskValue in enumerate((0x01, 0x02, 0x04)):
        if KindValue & MaskValue:
            Counts[Index], Cursor = Count(SourceData, Cursor)
    if SourceData[Cursor] != 0xFF:
        raise ValueError("trim total is missing")
    Total = struct.unpack_from("<I", SourceData, Cursor + 1)[0]
    Cursor += 5
    VectorValue = None
    if KindValue & 0x08:
        VectorValue = struct.unpack_from("<fff", SourceData, Cursor)
        Cursor += 12
    Lengths: list[int] = []
    LengthBudget = len(SourceData) - Cursor
    for _ in range(Counts[1] + Counts[2]):
        if LengthBudget <= 0:
            raise ValueError("trim lengths exceed the stream")
        Value, Cursor = Count(SourceData, Cursor)
        LengthBudget = len(SourceData) - Cursor
        Lengths.append(Value)
    if Total > max(0, len(SourceData) - Cursor) // max(1, Width):
        raise ValueError("trim handles exceed the stream")
    Handles, Cursor = ReadHandles(SourceData, Cursor, Total, Width)
    return (
        TrimRec(
            KindValue,
            Offset,
            (Counts[0], Counts[1], Counts[2]),
            Total,
            VectorValue,
            tuple(Lengths),
            Handles,
        ),
        Cursor,
    )


# this definition exists because focused behavior needs one stable owner
def ParseTrims(
    SourceData: bytes, EndOffset: int, Width: int, FaceCount: int
) -> tuple[TrimRec, ...]:
    Chain: list[TrimRec] = []
    Offset = EndOffset
    for _ in range(FaceCount):
        Found: tuple[int, TrimRec] | None = None
        for Start in range(Offset - 1, -1, -1):
            if SourceData[Start] != 0x01 or SourceData[Start + 1] not in KTrimKinds:
                continue
            try:
                TrimValue, NextOffset = ParseTrim(SourceData, Start, Width)
            except (IndexError, struct.error, ValueError):
                continue
            if NextOffset == Offset:
                Found = (Start, TrimValue)
                break
        if Found is None:
            raise ValueError("trim chain is incomplete")
        Offset, TrimValue = Found
        Chain.append(TrimValue)
    Chain.reverse()
    return tuple(Chain)


# this definition exists because focused behavior needs one stable owner
def ParseEdge(
    SourceData: bytes, Offset: int, Width: int
) -> tuple[tuple[EdgeRec, ...], int]:
    RowValues: list[EdgeRec] = []
    Cursor = Offset
    while Cursor < len(SourceData) and SourceData[Cursor] == 0x01:
        KindValue = SourceData[Cursor + 1]
        if KindValue not in (0x01, 0x02):
            break
        CountValue, Cursor = Count(SourceData, Cursor + 2)
        for _ in range(CountValue):
            if SourceData[Cursor] != 0x02:
                raise ValueError("edge row is missing")
            Arity = SourceData[Cursor + 1]
            Cursor += 2
            Handles = tuple(
                int.from_bytes(
                    SourceData[Cursor + Width * Index : Cursor + Width * (Index + 1)],
                    "big",
                )
                for Index in range(Arity)
            )
            Cursor += Arity * Width
            RowValues.append(EdgeRec(Arity, Handles, Cursor - Arity * Width - 2))
        if SourceData[Cursor : Cursor + 8] == KDelimiter:
            Cursor += 8
    return tuple(RowValues), Cursor


# this definition exists because focused behavior needs one stable owner
def ParseVert(SourceData: bytes, Offset: int) -> tuple[tuple[VertRec, ...], int]:
    if SourceData[Offset : Offset + 2] != b"\x01\x06":
        raise ValueError("vertex table is missing")
    CountValue, Cursor = Count(SourceData, Offset + 2)
    RowValues: list[VertRec] = []
    for _ in range(CountValue):
        if SourceData[Cursor : Cursor + 3] != b"\x05\x08\x01":
            raise ValueError("vertex row is missing")
        Point = struct.unpack_from("<fff", SourceData, Cursor + 3)
        RowValues.append(VertRec(Point, Cursor))
        Cursor += 15
    return tuple(RowValues), Cursor


# this definition exists because focused behavior needs one stable owner
def ParseRoster(SourceData: bytes) -> tuple[VertRec, ...]:
    EndOffset = len(SourceData)
    while EndOffset >= 7 and SourceData[EndOffset - 7] != 0x54:
        EndOffset -= 1
    RowValues: list[VertRec] = []
    while (
        EndOffset >= 7
        and SourceData[EndOffset - 7] == 0x54
        and SourceData[EndOffset - 3 : EndOffset] == b"\x00\x00\x00"
    ):
        Start = EndOffset - 7
        RowValues.append(VertRec((0.0, 0.0, 0.0), Start))
        EndOffset = Start
    RowValues.reverse()
    return tuple(RowValues)


# this definition exists because focused behavior needs one stable owner
def ExpandTri(TrimValue: TrimRec) -> tuple[tuple[int, int, int], ...]:
    Handles = TrimValue.handles
    CountA, CountB, CountC = TrimValue.counts
    Triangles: list[tuple[int, int, int]] = []
    Cursor = 0
    for _ in range(CountA):
        Triangles.append((Handles[Cursor], Handles[Cursor + 1], Handles[Cursor + 2]))
        Cursor += 3
    for Length in TrimValue.lengths[:CountB]:
        for Index in range(Length - 2):
            First = Handles[Cursor + Index]
            Second = Handles[Cursor + Index + 1]
            Third = Handles[Cursor + Index + 2]
            Triangles.append(
                (First, Second, Third) if Index % 2 == 0 else (Second, First, Third)
            )
        Cursor += Length
    for Length in TrimValue.lengths[CountB : CountB + CountC]:
        Pivot = Handles[Cursor]
        for Index in range(1, Length - 1):
            Triangles.append(
                (Pivot, Handles[Cursor + Index], Handles[Cursor + Index + 1])
            )
        Cursor += Length
    return tuple(Triangles)


# this definition exists because focused behavior needs one stable owner
def WalkCycleMut(
    Start: int,
    EndOffset: int,
    NextByStart: dict[int, list[int]],
    UsedPairs: set[tuple[int, int]],
) -> tuple[int, ...]:
    Cycle = [Start]
    Current = EndOffset
    UsedPairs.add((Start, EndOffset))
    while Current != Start:
        Cycle.append(Current)
        Options = [
            Value
            for Value in NextByStart.get(Current, ())
            if (Current, Value) not in UsedPairs
        ]
        if not Options:
            break
        Value = Options[0]
        UsedPairs.add((Current, Value))
        Current = Value
    if Current == Start and len(Cycle) >= 3:
        return tuple(Cycle)
    return ()


# this definition exists because focused behavior needs one stable owner
def Boundary(TrimValue: TrimRec) -> tuple[tuple[int, ...], ...]:
    Directed: set[tuple[int, int]] = set()
    for First, Second, Third in ExpandTri(TrimValue):
        for Start, EndOffset in ((First, Second), (Second, Third), (Third, First)):
            if Start != EndOffset:
                Directed.add((Start, EndOffset))
    BoundaryEdges = [
        EdgeValue
        for EdgeValue in Directed
        if (EdgeValue[1], EdgeValue[0]) not in Directed
    ]
    NextByStart: dict[int, list[int]] = {}
    for Start, EndOffset in BoundaryEdges:
        NextByStart.setdefault(Start, []).append(EndOffset)
    Cycles: list[tuple[int, ...]] = []
    UsedPairs: set[tuple[int, int]] = set()
    for Start, EndOffset in BoundaryEdges:
        if (Start, EndOffset) in UsedPairs:
            continue
        Cycle = WalkCycleMut(Start, EndOffset, NextByStart, UsedPairs)
        if Cycle:
            Cycles.append(Cycle)
    return tuple(Cycles)
