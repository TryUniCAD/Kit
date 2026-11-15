from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from convert.adapters.creo.Stream import ReadCompactAt
from convert.adapters.creo.Stream import ScanFields
from convert.adapters.creo.Stream import StreamNode
from convert.adapters.creo.Stream import StreamParser

KPlaneType = 34
KPrototypeWindow = 12
KLocalConstants = {0x0F: 1.0, 0x18: 0.0, 0x10: -1.0}


@dataclass(frozen=True, slots=True)
class CreoSurface:
    geom_id: int
    geom_type: int
    feature_id: int | None
    envelope: tuple[float, ...]
    outline: tuple[float, ...]
    local_system: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class CreoCurve:
    curve_id: int
    curve_type: int
    feature_id: int | None
    points: tuple[float, ...]
    face_ids: tuple[int | None, int | None]
    next_curve_ids: tuple[int | None, int | None]


@dataclass(frozen=True, slots=True)
class CreoMassProperties:
    volume: float | None
    centroid: tuple[float, float, float] | None
    minimum: tuple[float, float, float] | None
    maximum: tuple[float, float, float] | None
    vertex_count: int
    valid: bool


@dataclass(frozen=True, slots=True)
class CreoTopology:
    face_count: int
    closed_loop_count: int
    shell_count: int
    solid_count: int
    valid: bool


@dataclass(frozen=True, slots=True)
class CreoLogicalObject:
    object_id: int
    object_type: int | None
    object_subtype: int | None
    feature_id: int | None
    next_object_id: int | None


def ReadDoubleAt(DataValue: bytes, Position: int) -> tuple[float | None, int]:
    if Position >= len(DataValue):
        return None, Position
    TokenValue = DataValue[Position]
    if TokenValue in KLocalConstants:
        return KLocalConstants[TokenValue], Position + 1
    if TokenValue in (0x2D, 0x46):
        LeadValue = b"\x40" if TokenValue == 0x46 else b"\xC0"
        return (
            struct.unpack(">d", LeadValue + DataValue[Position + 1 : Position + 8])[0],
            Position + 8,
        )
    if TokenValue == 0x52:
        return struct.unpack(">d", DataValue[Position + 1 : Position + 9])[0], Position + 9
    return None, Position


def DecodeLocalSystem(
    DataValue: bytes, Offset: int
) -> tuple[tuple[float, ...], int]:
    Position = Offset
    if Position < len(DataValue) and DataValue[Position] == 0xF9:
        _RowsValue, Position = ReadCompactAt(DataValue, Position + 1)
        _ColsValue, Position = ReadCompactAt(DataValue, Position)
    Values: list[float] = []
    while len(Values) < 12 and Position < len(DataValue):
        TokenValue = DataValue[Position]
        if 0xE4 <= TokenValue <= 0xE6 and Values:
            Values.extend([Values[-1]] * (TokenValue - 0xE3))
            Position += 1
            continue
        Value, NextPosition = ReadDoubleAt(DataValue, Position)
        if Value is None:
            break
        Values.append(Value)
        Position = NextPosition
    if len(Values) < 9:
        return (), Position
    return tuple(Values[:12]), Position


def NumberValues(Value: object) -> tuple[float, ...]:
    if isinstance(Value, list):
        return tuple(
            float(Item) for Item in Value if isinstance(Item, (int, float))
        )
    return ()


def FindNumber(Nodes: list[StreamNode], Index: int, Name: str) -> int | None:
    for Node in Nodes[Index + 1 : Index + KPrototypeWindow]:
        if Node.name == Name and isinstance(Node.value, int):
            return Node.value
    return None


def FindValues(Nodes: list[StreamNode], Index: int, Name: str) -> tuple[float, ...]:
    for Node in Nodes[Index + 1 : Index + KPrototypeWindow]:
        if Node.name == Name:
            return NumberValues(Node.value)
    return ()


def ElementBoundaries(DataValue: bytes) -> dict[int, int]:
    Fields = ScanFields(DataValue)
    Names = [Field.name for Field in Fields]
    if "srf_array" not in Names:
        return {}
    SrfIndex = Names.index("srf_array")
    GeomIndex = next(
        Index
        for Index, Name in enumerate(Names)
        if Name == "geom_id" and Index > SrfIndex
    )
    CrvIdIndex: int | None = None
    if "crv_array" in Names and "crv_id" in Names:
        CrvIndex = Names.index("crv_array")
        CrvIdIndex = next(
            Index
            for Index, Name in enumerate(Names)
            if Name == "crv_id" and Index > CrvIndex
        )
    Boundaries: dict[int, int] = {}
    for OffsetValue in range(len(DataValue) - 1):
        if DataValue[OffsetValue] != 0xE3:
            continue
        _FeatureValue, AfterValue = ReadCompactAt(DataValue, OffsetValue + 1)
        if AfterValue <= OffsetValue + 1:
            continue
        if AfterValue + 1 < len(DataValue) and DataValue[AfterValue + 1] == 0x4A:
            Width = 1 if DataValue[OffsetValue + 1] <= 0x7F else 2
            SecondValue = DataValue[OffsetValue + 1 + Width]
            if SecondValue == 0x22:
                Boundaries[OffsetValue] = GeomIndex
            elif CrvIdIndex is not None:
                Boundaries[OffsetValue] = CrvIdIndex
    if "lo_array" in Names and "lo_id" in Names:
        LoIndex = Names.index("lo_array")
        LoIdIndex = next(
            Index
            for Index, Name in enumerate(Names)
            if Name == "lo_id" and Index > LoIndex
        )
        for OffsetValue in range(len(DataValue) - 5):
            if DataValue[OffsetValue] != 0xE3:
                continue
            _FeatureValue, AfterValue = ReadCompactAt(DataValue, OffsetValue + 1)
            if AfterValue + 4 >= len(DataValue):
                continue
            if (
                DataValue[AfterValue] == 0x82
                and DataValue[AfterValue + 2] == 0x82
                and DataValue[AfterValue + 4] == 0x4A
            ):
                Boundaries[OffsetValue] = LoIdIndex
    return Boundaries


def FindLocalSystem(
    Nodes: list[StreamNode], Index: int, DataValue: bytes
) -> tuple[float, ...]:
    for Node in Nodes[Index + 1 : Index + KPrototypeWindow]:
        if Node.name == "local_sys":
            Values, _EndValue = DecodeLocalSystem(DataValue, Node.offset)
            return Values
    return ()


def ReadGeometry(
    DataValue: bytes,
) -> tuple[tuple[CreoSurface, ...], tuple[CreoCurve, ...]]:
    Nodes = StreamParser(DataValue, ElementBoundaries(DataValue)).Run()
    Surfaces: list[CreoSurface] = []
    Curves: list[CreoCurve] = []
    for Index, Node in enumerate(Nodes):
        if Node.name == "geom_id" and isinstance(Node.value, int):
            TypeValue = FindNumber(Nodes, Index, "geom_type")
            if TypeValue != KPlaneType:
                continue
            Surfaces.append(
                CreoSurface(
                    Node.value,
                    TypeValue,
                    FindNumber(Nodes, Index, "feat_id"),
                    FindValues(Nodes, Index, "envlp"),
                    FindValues(Nodes, Index, "outline"),
                    FindLocalSystem(Nodes, Index, DataValue),
                )
            )
        if Node.name == "crv_id" and isinstance(Node.value, int):
            Curves.append(
                CreoCurve(
                    Node.value,
                    FindNumber(Nodes, Index, "type") or 0,
                    FindNumber(Nodes, Index, "feat_id"),
                    FindValues(Nodes, Index, "crv_pnt_arr"),
                    (
                        FindNumber(Nodes, Index, "crv_hdr_geom_ptr[0]"),
                        FindNumber(Nodes, Index, "crv_hdr_geom_ptr[1]"),
                    ),
                    (
                        FindNumber(Nodes, Index, "next_crv_hdr_ptr[0]"),
                        FindNumber(Nodes, Index, "next_crv_hdr_ptr[1]"),
                    ),
                )
            )
    return tuple(Surfaces), tuple(Curves)


def Dot(
    LeftValue: tuple[float, float, float],
    RightValue: tuple[float, float, float],
) -> float:
    return (
        LeftValue[0] * RightValue[0]
        + LeftValue[1] * RightValue[1]
        + LeftValue[2] * RightValue[2]
    )


def Cross(
    LeftValue: tuple[float, float, float], RightValue: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        LeftValue[1] * RightValue[2] - LeftValue[2] * RightValue[1],
        LeftValue[2] * RightValue[0] - LeftValue[0] * RightValue[2],
        LeftValue[0] * RightValue[1] - LeftValue[1] * RightValue[0],
    )


def Sub(
    LeftValue: tuple[float, float, float], RightValue: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        LeftValue[0] - RightValue[0],
        LeftValue[1] - RightValue[1],
        LeftValue[2] - RightValue[2],
    )


def Normalize(Value: tuple[float, float, float]) -> tuple[float, float, float] | None:
    LengthValue = math.sqrt(Dot(Value, Value))
    if LengthValue <= 1e-12:
        return None
    return (Value[0] / LengthValue, Value[1] / LengthValue, Value[2] / LengthValue)


def PlaneValue(Surface: CreoSurface) -> tuple[tuple[float, float, float], float] | None:
    Values = Surface.local_system
    if len(Values) < 12:
        return None
    NormalValue = Normalize((Values[6], Values[7], Values[8]))
    if NormalValue is None:
        return None
    OriginValue = (Values[9], Values[10], Values[11])
    return NormalValue, Dot(NormalValue, OriginValue)


def IntersectPlanes(
    First: tuple[tuple[float, float, float], float],
    Second: tuple[tuple[float, float, float], float],
    Third: tuple[tuple[float, float, float], float],
) -> tuple[float, float, float] | None:
    NormalValue = Cross(First[0], Second[0])
    DeterminantValue = Dot(NormalValue, Third[0])
    if abs(DeterminantValue) <= 1e-12:
        return None
    CrossValue = Cross(Second[0], Third[0])
    FirstScale = First[1] / DeterminantValue
    SecondScale = Second[1] / DeterminantValue
    ThirdScale = Third[1] / DeterminantValue
    return (
        FirstScale * CrossValue[0]
        + SecondScale * Cross(Third[0], First[0])[0]
        + ThirdScale * Cross(First[0], Second[0])[0],
        FirstScale * CrossValue[1]
        + SecondScale * Cross(Third[0], First[0])[1]
        + ThirdScale * Cross(First[0], Second[0])[1],
        FirstScale * CrossValue[2]
        + SecondScale * Cross(Third[0], First[0])[2]
        + ThirdScale * Cross(First[0], Second[0])[2],
    )


def ReadMassProperties(Surfaces: tuple[CreoSurface, ...]) -> CreoMassProperties:
    Planes = [PlaneValue(Surface) for Surface in Surfaces]
    Planes = [Plane for Plane in Planes if Plane is not None]
    if len(Planes) < 4:
        return CreoMassProperties(None, None, None, None, 0, False)
    Framed = [
        Surface for Surface in Surfaces if len(Surface.local_system) >= 12
    ]
    AverageOrigin = (
        sum(Surface.local_system[9] for Surface in Framed) / len(Framed),
        sum(Surface.local_system[10] for Surface in Framed) / len(Framed),
        sum(Surface.local_system[11] for Surface in Framed) / len(Framed),
    )
    Oriented: list[tuple[tuple[float, float, float], float]] = []
    for NormalValue, OffsetValue in Planes:
        if Dot(NormalValue, AverageOrigin) - OffsetValue > 0.0:
            Oriented.append(
                (
                    (-NormalValue[0], -NormalValue[1], -NormalValue[2]),
                    -OffsetValue,
                )
            )
        else:
            Oriented.append((NormalValue, OffsetValue))
    Vertices: list[tuple[float, float, float]] = []
    for FirstIndex in range(len(Oriented)):
        for SecondIndex in range(FirstIndex + 1, len(Oriented)):
            for ThirdIndex in range(SecondIndex + 1, len(Oriented)):
                PointValue = IntersectPlanes(
                    Oriented[FirstIndex], Oriented[SecondIndex], Oriented[ThirdIndex]
                )
                if PointValue is None:
                    continue
                if all(
                    Dot(NormalValue, PointValue) <= OffsetValue + 1e-6
                    for NormalValue, OffsetValue in Oriented
                ):
                    if not any(
                        math.dist(PointValue, Existing) < 1e-6 for Existing in Vertices
                    ):
                        Vertices.append(PointValue)
    if len(Vertices) < 4:
        return CreoMassProperties(None, None, None, None, len(Vertices), False)
    MinimumValue = (
        min(Vertex[0] for Vertex in Vertices),
        min(Vertex[1] for Vertex in Vertices),
        min(Vertex[2] for Vertex in Vertices),
    )
    MaximumValue = (
        max(Vertex[0] for Vertex in Vertices),
        max(Vertex[1] for Vertex in Vertices),
        max(Vertex[2] for Vertex in Vertices),
    )
    VolumeTotal = 0.0
    CentroidTotal = [0.0, 0.0, 0.0]
    for NormalValue, OffsetValue in Oriented:
        OnPlane = [
            Vertex
            for Vertex in Vertices
            if abs(Dot(NormalValue, Vertex) - OffsetValue) < 1e-6
        ]
        if len(OnPlane) < 3:
            continue
        CenterValue = (
            sum(Vertex[0] for Vertex in OnPlane) / len(OnPlane),
            sum(Vertex[1] for Vertex in OnPlane) / len(OnPlane),
            sum(Vertex[2] for Vertex in OnPlane) / len(OnPlane),
        )
        ReferenceValue = Sub(OnPlane[0], CenterValue)
        Ordered = sorted(
            OnPlane,
            key=lambda Vertex: math.atan2(
                Dot(Cross(ReferenceValue, Sub(Vertex, CenterValue)), NormalValue),
                Dot(ReferenceValue, Sub(Vertex, CenterValue)),
            ),
        )
        for IndexValue in range(1, len(Ordered) - 1):
            First = Ordered[0]
            Second = Ordered[IndexValue]
            Third = Ordered[IndexValue + 1]
            TetraVolume = Dot(First, Cross(Second, Third)) / 6.0
            VolumeTotal += TetraVolume
            CentroidTotal[0] += TetraVolume * (First[0] + Second[0] + Third[0]) / 4.0
            CentroidTotal[1] += TetraVolume * (First[1] + Second[1] + Third[1]) / 4.0
            CentroidTotal[2] += TetraVolume * (First[2] + Second[2] + Third[2]) / 4.0
    if abs(VolumeTotal) <= 1e-9:
        return CreoMassProperties(
            None, None, MinimumValue, MaximumValue, len(Vertices), False
        )
    VolumeValue = abs(VolumeTotal)
    SignValue = 1.0 if VolumeTotal > 0.0 else -1.0
    CentroidValue = (
        SignValue * CentroidTotal[0] / VolumeValue,
        SignValue * CentroidTotal[1] / VolumeValue,
        SignValue * CentroidTotal[2] / VolumeValue,
    )
    return CreoMassProperties(
        VolumeValue,
        CentroidValue,
        MinimumValue,
        MaximumValue,
        len(Vertices),
        True,
    )


def ReadTopology(
    Curves: tuple[CreoCurve, ...], SurfaceCount: int
) -> CreoTopology:
    ById = {Curve.curve_id: Curve for Curve in Curves}
    FaceSlots: dict[int, list[tuple[int, int]]] = {}
    SharedEdges = 0
    for Curve in Curves:
        Left, Right = Curve.face_ids
        if Left is not None and Right is not None:
            SharedEdges += 1
        for Slot, FaceValue in enumerate(Curve.face_ids):
            if FaceValue is not None:
                FaceSlots.setdefault(FaceValue, []).append((Curve.curve_id, Slot))
    ClosedLoops = 0
    for FaceValue, Entries in FaceSlots.items():
        StartValue = Entries[0]
        CurrentValue = StartValue
        Visited: set[tuple[int, int]] = set()
        IsClosed = False
        for _ in range(len(Entries) + 1):
            if CurrentValue in Visited:
                IsClosed = CurrentValue == StartValue
                break
            Visited.add(CurrentValue)
            CurveValue = ById.get(CurrentValue[0])
            if CurveValue is None:
                break
            NextValue = CurveValue.next_curve_ids[CurrentValue[1]]
            if NextValue is None:
                break
            NextCurve = ById.get(NextValue)
            if NextCurve is None:
                break
            if NextCurve.face_ids[0] == FaceValue:
                NextSlot = 0
            elif NextCurve.face_ids[1] == FaceValue:
                NextSlot = 1
            else:
                break
            CurrentValue = (NextValue, NextSlot)
        if IsClosed:
            ClosedLoops += 1
    Adjacency: dict[int, set[int]] = {Face: set() for Face in FaceSlots}
    for Curve in Curves:
        Left, Right = Curve.face_ids
        if Left is not None and Right is not None:
            Adjacency.setdefault(Left, set()).add(Right)
            Adjacency.setdefault(Right, set()).add(Left)
    Components = 0
    Seen: set[int] = set()
    for Face in Adjacency:
        if Face in Seen:
            continue
        Components += 1
        Stack = [Face]
        while Stack:
            Current = Stack.pop()
            if Current in Seen:
                continue
            Seen.add(Current)
            Stack.extend(Adjacency.get(Current, ()))
    IsSolid = (
        SurfaceCount > 0
        and ClosedLoops == len(FaceSlots)
        and SharedEdges == len(Curves)
        and Components > 0
    )
    ShellCount = Components if IsSolid else 0
    return CreoTopology(
        face_count=SurfaceCount,
        closed_loop_count=ClosedLoops,
        shell_count=ShellCount,
        solid_count=ShellCount,
        valid=IsSolid,
    )


def ReadLogicalObjects(DataValue: bytes) -> tuple[CreoLogicalObject, ...]:
    Nodes = StreamParser(DataValue, ElementBoundaries(DataValue)).Run()
    Objects: list[CreoLogicalObject] = []
    for Index, Node in enumerate(Nodes):
        if Node.name != "lo_id" or not isinstance(Node.value, int):
            continue
        NextValue: int | None = None
        TypeValue: int | None = None
        SubtypeValue: int | None = None
        FeatureValue: int | None = None
        for Candidate in Nodes[Index + 1 : Index + 9]:
            if Candidate.name == "lo_type" and isinstance(Candidate.value, int):
                TypeValue = Candidate.value
            elif Candidate.name == "lo_subtype" and isinstance(Candidate.value, int):
                SubtypeValue = Candidate.value
            elif Candidate.name == "feat_id" and isinstance(Candidate.value, int):
                FeatureValue = Candidate.value
            elif Candidate.name == "next_lo_ptr" and isinstance(Candidate.value, int):
                NextValue = Candidate.value
                break
        Objects.append(
            CreoLogicalObject(
                Node.value, TypeValue, SubtypeValue, FeatureValue, NextValue
            )
        )
    return tuple(Objects)
