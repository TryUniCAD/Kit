from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.creo.Stream import ReadCompactAt
from convert.adapters.creo.Stream import ScanFields
from convert.adapters.creo.Stream import StreamNode
from convert.adapters.creo.Stream import StreamParser

KPlaneType = 34
KPrototypeWindow = 12


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
    if "srf_array" not in Names or "crv_array" not in Names:
        return {}
    SrfIndex = Names.index("srf_array")
    CrvIndex = Names.index("crv_array")
    GeomIndex = next(
        Index
        for Index, Name in enumerate(Names)
        if Name == "geom_id" and Index > SrfIndex
    )
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
            Boundaries[OffsetValue] = GeomIndex if SecondValue == 0x22 else CrvIdIndex
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
                    FindValues(Nodes, Index, "local_sys"),
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
