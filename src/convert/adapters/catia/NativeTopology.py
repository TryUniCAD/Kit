from __future__ import annotations

from dataclasses import dataclass
import struct

KDelimiter = b"\x10\x24\x04\xff\xff\x00\x00\x00"
KTrimKinds = frozenset(range(0x40, 0x50))


@dataclass(frozen=True, slots=True)
class TrimRec:
    kind: int
    offset: int
    counts: tuple[int, int, int]
    total: int
    vector: tuple[float, float, float] | None
    lengths: tuple[int, ...]
    handles: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class EdgeRec:
    arity: int
    handles: tuple[int, ...]
    offset: int


@dataclass(frozen=True, slots=True)
class VertRec:
    point: tuple[float, float, float]
    offset: int


def Count(Data: bytes, Offset: int) -> tuple[int, int]:
    Value = Data[Offset]
    if Value != 0xFF:
        return Value, Offset + 1
    return struct.unpack_from("<I", Data, Offset + 1)[0], Offset + 5


def FindFbb(Data: bytes) -> tuple[int, int]:
    BestOffset = -1
    BestCount = 0
    for Offset in range(len(Data) - 4):
        if Data[Offset : Offset + 4] not in (b"\x30\x04\x04\xff", b"\xb0\x04\x04\xff"):
            continue
        CountValue = 0
        Cursor = Offset
        while Data[Cursor : Cursor + 4] in (b"\x30\x04\x04\xff", b"\xb0\x04\x04\xff"):
            CountValue += 1
            Cursor += 8
        if CountValue > BestCount:
            BestOffset = Offset
            BestCount = CountValue
    if BestOffset < 0:
        raise ValueError("FBB spine is missing")
    return BestOffset, BestCount


def ParseTrim(Data: bytes, Offset: int, Width: int) -> tuple[TrimRec, int]:
    if Data[Offset] != 0x01 or Data[Offset + 1] not in KTrimKinds:
        raise ValueError("trim marker is missing")
    Kind = Data[Offset + 1]
    Cursor = Offset + 2
    Counts = [0, 0, 0]
    for Index, Mask in enumerate((0x01, 0x02, 0x04)):
        if Kind & Mask:
            Counts[Index], Cursor = Count(Data, Cursor)
    if Data[Cursor] != 0xFF:
        raise ValueError("trim total is missing")
    Total = struct.unpack_from("<I", Data, Cursor + 1)[0]
    Cursor += 5
    VectorValue = None
    if Kind & 0x08:
        VectorValue = struct.unpack_from("<fff", Data, Cursor)
        Cursor += 12
    Lengths: list[int] = []
    for _ in range(Counts[1] + Counts[2]):
        Value, Cursor = Count(Data, Cursor)
        Lengths.append(Value)
    Handles: list[int] = []
    for _ in range(Total):
        Handles.append(int.from_bytes(Data[Cursor : Cursor + Width], "big"))
        Cursor += Width
    return (
        TrimRec(
            Kind,
            Offset,
            (Counts[0], Counts[1], Counts[2]),
            Total,
            VectorValue,
            tuple(Lengths),
            tuple(Handles),
        ),
        Cursor,
    )


def ParseTrims(
    Data: bytes, End: int, Width: int, FaceCount: int
) -> tuple[TrimRec, ...]:
    Chain: list[TrimRec] = []
    Offset = End
    for _ in range(FaceCount):
        Found: tuple[int, TrimRec] | None = None
        for Start in range(Offset - 1, -1, -1):
            if Data[Start] != 0x01 or Data[Start + 1] not in KTrimKinds:
                continue
            try:
                TrimValue, NextOffset = ParseTrim(Data, Start, Width)
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


def ParseEdge(Data: bytes, Offset: int, Width: int) -> tuple[tuple[EdgeRec, ...], int]:
    Rows: list[EdgeRec] = []
    Cursor = Offset
    while Cursor < len(Data) and Data[Cursor] == 0x01:
        Kind = Data[Cursor + 1]
        if Kind not in (0x01, 0x02):
            break
        CountValue, Cursor = Count(Data, Cursor + 2)
        for _ in range(CountValue):
            if Data[Cursor] != 0x02:
                raise ValueError("edge row is missing")
            Arity = Data[Cursor + 1]
            Cursor += 2
            Handles = tuple(
                int.from_bytes(
                    Data[Cursor + Width * Index : Cursor + Width * (Index + 1)], "big"
                )
                for Index in range(Arity)
            )
            Cursor += Arity * Width
            Rows.append(EdgeRec(Arity, Handles, Cursor - Arity * Width - 2))
        if Data[Cursor : Cursor + 8] == KDelimiter:
            Cursor += 8
    return tuple(Rows), Cursor


def ParseVert(Data: bytes, Offset: int) -> tuple[tuple[VertRec, ...], int]:
    if Data[Offset : Offset + 2] != b"\x01\x06":
        raise ValueError("vertex table is missing")
    CountValue, Cursor = Count(Data, Offset + 2)
    Rows: list[VertRec] = []
    for _ in range(CountValue):
        if Data[Cursor : Cursor + 3] != b"\x05\x08\x01":
            raise ValueError("vertex row is missing")
        Point = struct.unpack_from("<fff", Data, Cursor + 3)
        Rows.append(VertRec(Point, Cursor))
        Cursor += 15
    return tuple(Rows), Cursor


def ParseRoster(Data: bytes) -> tuple[VertRec, ...]:
    End = len(Data)
    while End >= 7 and Data[End - 7] != 0x54:
        End -= 1
    Rows: list[VertRec] = []
    while End >= 7 and Data[End - 7] == 0x54 and Data[End - 3 : End] == b"\x00\x00\x00":
        Start = End - 7
        Rows.append(VertRec((0.0, 0.0, 0.0), Start))
        End = Start
    Rows.reverse()
    return tuple(Rows)


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


def Boundary(TrimValue: TrimRec) -> tuple[tuple[int, ...], ...]:
    Directed: set[tuple[int, int]] = set()
    for First, Second, Third in ExpandTri(TrimValue):
        for Start, End in ((First, Second), (Second, Third), (Third, First)):
            if Start != End:
                Directed.add((Start, End))
    BoundaryEdges = [Edge for Edge in Directed if (Edge[1], Edge[0]) not in Directed]
    NextByStart: dict[int, list[int]] = {}
    for Start, End in BoundaryEdges:
        NextByStart.setdefault(Start, []).append(End)
    Cycles: list[tuple[int, ...]] = []
    Used: set[tuple[int, int]] = set()
    for Start, End in BoundaryEdges:
        if (Start, End) in Used:
            continue
        Cycle = [Start]
        Current = End
        Used.add((Start, End))
        while Current != Start:
            Cycle.append(Current)
            Options = [
                Value
                for Value in NextByStart.get(Current, ())
                if (Current, Value) not in Used
            ]
            if not Options:
                break
            Value = Options[0]
            Used.add((Current, Value))
            Current = Value
        if Current == Start and len(Cycle) >= 3:
            Cycles.append(tuple(Cycle))
    return tuple(Cycles)
