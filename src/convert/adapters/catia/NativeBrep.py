from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
import math
import struct

from convert.adapters.catia.Container import CfvTwoArchive, CfvTwoFolder, CfvTwoStream
from convert.adapters.catia.NativeSurface import (
    AxisFromCarrier,
    KSurfaceKinds,
    MakeSurf,
    ParseSurf,
    SurfaceRec,
)
from convert.adapters.catia.NativeTopology import (
    Boundary,
    EdgeRec,
    FindFbb,
    ParseEdge,
    ParseRoster,
    ParseTrims,
    ParseVert,
    TrimRec,
    VertRec,
)
from interchange import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    CircleCurve,
    Diagnostic,
    LineCurve,
    Severity,
    SpaceVector,
)

# this binding exists because shared behavior needs one stable value
KBodyId = "catia:body:1"

# this binding exists because one probe handle rejects a wrong pooled surface
KPoolProbe = 0.5

# this binding exists because shared behavior needs one stable value
KTrimSurfaces = {
    0x41: frozenset({0x34, 0x38}),
    0x42: frozenset({0x33, 0x34, 0x38}),
    0x43: frozenset({0x33, 0x34, 0x35, 0x38}),
    0x44: frozenset({0x34}),
    0x45: frozenset({0x34}),
    0x46: frozenset({0x34}),
    0x47: frozenset({0x33, 0x34, 0x35}),
    0x4A: frozenset({0x32}),
    0x4B: frozenset({0x32}),
    0x4C: frozenset({0x32}),
    0x4D: frozenset({0x32}),
    0x4E: frozenset({0x32}),
    0x4F: frozenset({0x32}),
}


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class BrepData:
    surfaces: tuple[SurfaceRec, ...]
    trims: tuple[TrimRec, ...]
    edges: tuple[EdgeRec, ...]
    vertices: tuple[VertRec, ...]
    roster: tuple[VertRec, ...]
    width: int
    tessellation: tuple[tuple[float, float], ...] = ()
    heuristic: bool = False


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class FaceBuild:
    curves: tuple[LineCurve | CircleCurve, ...]
    edges: tuple[BrepEdge, ...]
    coedges: tuple[BrepCoedge, ...]
    loops: tuple[BrepLoop, ...]
    face: BrepFace


# this definition exists because focused behavior needs one stable owner
def Vector(Values: tuple[float, float, float]) -> SpaceVector:
    return SpaceVector(*Values)


# this definition exists because focused behavior needs one stable owner
def Normalize(Values: tuple[float, float, float]) -> tuple[float, float, float]:
    Length = math.sqrt(sum(Value * Value for Value in Values))
    if Length <= 1e-12:
        return (1.0, 0.0, 0.0)
    return (
        Values[0] / Length,
        Values[1] / Length,
        Values[2] / Length,
    )


# this definition exists because focused behavior needs one stable owner
def Largest(Folder: CfvTwoFolder, NameValue: str) -> CfvTwoStream:
    Matches = tuple(Stream for Stream in Folder.streams if Stream.name == NameValue)
    if not Matches:
        raise ValueError(f"{NameValue} stream is missing")

    # this callback exists because the directory lists duplicate logical names
    return max(Matches, key=lambda Stream: Stream.logical_length)


# this definition exists because focused behavior needs one stable owner
def ParseSurfaces(SourceData: bytes) -> list[SurfaceRec]:
    Surfaces: list[SurfaceRec] = []
    EndValue = -1
    for Marker in range(len(SourceData) - 5):
        if SourceData[Marker : Marker + 2] != b"\x00\x33":
            continue
        if SourceData[Marker + 2] not in KSurfaceKinds:
            continue
        Offset = Marker - 2
        if Offset < EndValue:
            continue
        try:
            SurfaceValue, NextOffset = ParseSurf(SourceData, Offset)
        except (IndexError, ValueError):
            continue
        if SurfaceValue.sign not in (1, -1):
            continue
        if not all(
            math.isfinite(Value) and abs(Value) < 1e6 for Value in SurfaceValue.bounds
        ):
            continue
        Surfaces.append(SurfaceValue)
        EndValue = NextOffset
    return Surfaces


# this definition exists because focused behavior needs one stable owner
def ParseCircles(
    SourceData: bytes,
) -> tuple[tuple[int, int, tuple[float, float, float], float], ...]:
    RowValues: list[tuple[int, int, tuple[float, float, float], float]] = []
    Cursor = 0
    Limit = len(SourceData) - 8
    while Cursor <= Limit:
        if SourceData[Cursor] == 0x60:
            CountValue = SourceData[Cursor + 5]
            if (
                SourceData[Cursor + 6 : Cursor + 8] == b"\x00\x33"
                and SourceData[Cursor + 8] == 0x37
                and CountValue >= 18
                and Cursor + 9 + CountValue <= len(SourceData)
            ):
                DataValue = SourceData[Cursor + 9 : Cursor + 9 + CountValue]
                Center = struct.unpack_from(">3f", DataValue, 0)
                Radius = abs(struct.unpack_from(">f", DataValue, 12)[0])
                RowValues.append((DataValue[-2], DataValue[-1], Center, Radius))
                Cursor += 9 + CountValue
                continue
        if (
            SourceData[Cursor : Cursor + 2] == b"\x00\x33"
            and SourceData[Cursor + 2] == 0x37
        ):
            CountValue = SourceData[Cursor - 1]
            if CountValue >= 18 and Cursor + 3 + CountValue <= len(SourceData):
                DataValue = SourceData[Cursor + 3 : Cursor + 3 + CountValue]
                Center = struct.unpack_from(">3f", DataValue, 0)
                Radius = abs(struct.unpack_from(">f", DataValue, 12)[0])
                RowValues.append((DataValue[-2], DataValue[-1], Center, Radius))
                Cursor += 3 + CountValue
                continue
        Cursor += 1
    return tuple(RowValues)


# this definition exists because focused behavior needs one stable owner
def AssignPlanesMut(
    Surfaces: list[SurfaceRec],
    Trims: tuple[TrimRec, ...],
    Circles: tuple[tuple[int, int, tuple[float, float, float], float], ...],
    Planes: list[int],
    Assigned: list[int | None],
    LoadValue: dict[int, int],
) -> None:
    for FaceIndex, TrimValue in enumerate(Trims):
        if TrimValue.vector is None:
            continue
        Normal = Normalize(TrimValue.vector)
        Offsets = [
            sum(LeftValue * RightValue for LeftValue, RightValue in zip(Normal, Center))
            for FaceA, FaceB, Center, _ in Circles
            if FaceIndex in (FaceA, FaceB)
        ]
        if not Offsets:
            continue
        BestValue = None
        BestError = 1e9
        for Candidate in Planes:
            Center = Surfaces[Candidate].bounds[:3]
            Error = min(
                abs(
                    sum(
                        LeftValue * RightValue
                        for LeftValue, RightValue in zip(Normal, Center)
                    )
                    - Offset
                )
                for Offset in Offsets
            )
            if Error < BestError - 1e-6:
                BestError = Error
                BestValue = Candidate
        if BestValue is not None and BestError < 1e-2:
            Assigned[FaceIndex] = BestValue
            LoadValue[BestValue] = LoadValue.get(BestValue, 0) + 1


# this definition exists because focused behavior needs one stable owner
def AssignCylsMut(
    Surfaces: list[SurfaceRec],
    Trims: tuple[TrimRec, ...],
    Circles: tuple[tuple[int, int, tuple[float, float, float], float], ...],
    Cylinders: list[int],
    Assigned: list[int | None],
    LoadValue: dict[int, int],
) -> None:
    for FaceIndex, TrimValue in enumerate(Trims):
        if Assigned[FaceIndex] is not None:
            continue
        if TrimValue.kind not in (0x42, 0x43, 0x47):
            continue
        Radii = [
            Radius for FaceA, FaceB, _, Radius in Circles if FaceIndex in (FaceA, FaceB)
        ]
        if not Radii:
            continue
        BestValue = None
        BestError = 1e9
        for Candidate in Cylinders:
            Radius = abs(Surfaces[Candidate].params[5])
            Error = min(abs(Radius - Value) for Value in Radii)
            if Error < BestError - 1e-6:
                BestError = Error
                BestValue = Candidate
        if BestValue is not None and BestError < 1e-2:
            Assigned[FaceIndex] = BestValue
            LoadValue[BestValue] = LoadValue.get(BestValue, 0) + 1


# this definition exists because focused behavior needs one stable owner
def AssignRestMut(
    Surfaces: list[SurfaceRec],
    Trims: tuple[TrimRec, ...],
    Assigned: list[int | None],
    LoadValue: dict[int, int],
) -> None:
    for FaceIndex, TrimValue in enumerate(Trims):
        if Assigned[FaceIndex] is not None:
            continue
        Allowed = KTrimSurfaces.get(TrimValue.kind, frozenset(KSurfaceKinds))
        Candidates = [
            Index for Index, Value in enumerate(Surfaces) if Value.kind in Allowed
        ]
        if not Candidates:
            Candidates = list(range(len(Surfaces)))

        # this callback exists because pooled surfaces must stay balanced across faces
        BestValue = min(Candidates, key=lambda Value: LoadValue.get(Value, 0))
        Assigned[FaceIndex] = BestValue
        LoadValue[BestValue] = LoadValue.get(BestValue, 0) + 1


# this definition exists because focused behavior needs one stable owner
def AssignSurfaces(
    Surfaces: list[SurfaceRec],
    Trims: tuple[TrimRec, ...],
    SurfData: bytes,
) -> tuple[SurfaceRec, ...]:
    FaceCount = len(Trims)
    Circles = ParseCircles(SurfData)
    Cylinders: list[int] = []
    Planes: list[int] = []
    for Index, Value in enumerate(Surfaces):
        if Value.kind == 0x33 and len(Value.params) >= 6:
            Cylinders.append(Index)
        elif Value.kind == 0x32:
            Planes.append(Index)
    Assigned: list[int | None] = [None] * FaceCount
    LoadValue: dict[int, int] = {}
    AssignPlanesMut(Surfaces, Trims, Circles, Planes, Assigned, LoadValue)
    AssignCylsMut(Surfaces, Trims, Circles, Cylinders, Assigned, LoadValue)
    AssignRestMut(Surfaces, Trims, Assigned, LoadValue)
    if any(Value is None for Value in Assigned):
        raise ValueError("surface assignment is incomplete")
    return tuple(Surfaces[Value] for Value in Assigned if Value is not None)


# this definition exists because a pooled pool needs a distance to one surface only
def SurfDist(
    Point: tuple[float, float, float],
    SurfaceValue: SurfaceRec,
    Normal: tuple[float, float, float] | None,
) -> float:
    if SurfaceValue.kind == 0x32:
        if Normal is None:
            return math.inf
        Origin = SurfaceValue.bounds[0:3]
        return abs(
            sum(Normal[Index] * (Point[Index] - Origin[Index]) for Index in range(3))
        )
    Params = SurfaceValue.params
    if SurfaceValue.kind == 0x33 and len(Params) >= 6:
        AxisValue = AxisFromCarrier(Params)
        Delta = [Point[Index] - Params[Index] for Index in range(3)]
        Along = sum(Delta[Index] * AxisValue[Index] for Index in range(3))
        Radial = math.sqrt(max(0.0, sum(Value * Value for Value in Delta) - Along**2))
        return abs(Radial - abs(Params[5]))
    return math.inf


# this definition exists because a pooled cylinder pool is scored many times
def CylPool(
    PoolValues: list[SurfaceRec],
) -> list[
    tuple[
        SurfaceRec,
        tuple[float, float, float],
        tuple[float, float, float],
        float,
    ]
]:
    Cylinders: list[
        tuple[
            SurfaceRec,
            tuple[float, float, float],
            tuple[float, float, float],
            float,
        ]
    ] = []
    for Value in PoolValues:
        if Value.kind != 0x33 or len(Value.params) < 6:
            continue
        Params = Value.params
        Cylinders.append(
            (
                Value,
                AxisFromCarrier(Params),
                (Params[0], Params[1], Params[2]),
                abs(Params[5]),
            )
        )
    return Cylinders


# this definition exists because a plane face needs the best matching pooled plane
def BestPlane(
    Positions: dict[int, tuple[float, float, float]],
    TrimValue: TrimRec,
    Planes: list[SurfaceRec],
    KeepValue: SurfaceRec,
) -> SurfaceRec:
    Normal = TrimValue.vector
    if Normal is None:
        return KeepValue
    Handles = sorted(set(TrimValue.handles))
    BestCost: float | None = None
    for Value in Planes:
        if SurfDist(Positions[Handles[0]], Value, Normal) >= KPoolProbe:
            continue
        CostValue = sum(
            SurfDist(Positions[Handle], Value, Normal) for Handle in Handles
        )
        if BestCost is None or CostValue < BestCost - 1e-9:
            BestCost = CostValue
            KeepValue = Value
    return KeepValue


# this definition exists because a cylinder face needs the best matching pooled cylinder
def BestCyl(
    Positions: dict[int, tuple[float, float, float]],
    TrimValue: TrimRec,
    Cylinders: list[
        tuple[
            SurfaceRec,
            tuple[float, float, float],
            tuple[float, float, float],
            float,
        ]
    ],
    KeepValue: SurfaceRec,
) -> SurfaceRec:
    Handles = sorted(set(TrimValue.handles))
    BestCost: float | None = None
    for Value, AxisValue, Center, Radius in Cylinders:
        if CylDist(Positions[Handles[0]], AxisValue, Center, Radius) >= KPoolProbe:
            continue
        CostValue = sum(
            CylDist(Positions[Handle], AxisValue, Center, Radius) for Handle in Handles
        )
        if BestCost is None or CostValue < BestCost - 1e-9:
            BestCost = CostValue
            KeepValue = Value
    return KeepValue


# this definition exists because the pooled map is inferred and can be sharpened
def RefineMap(
    BrepValue: BrepData, PoolValues: list[SurfaceRec], Rounds: int | None = None
) -> tuple[SurfaceRec, ...]:
    if Rounds is None:
        Rounds = 2 if len(BrepValue.trims) <= 400 else 0
    Planes = [Value for Value in PoolValues if Value.kind == 0x32]
    Cylinders = CylPool(PoolValues)
    Current = list(BrepValue.surfaces)
    for _ in range(Rounds):
        Positions = PlaceRough(replace(BrepValue, surfaces=tuple(Current)))
        Updated = list(Current)
        for FaceIndex, TrimValue in enumerate(BrepValue.trims):
            KeepValue = Current[FaceIndex]
            if KeepValue.kind == 0x32:
                Updated[FaceIndex] = BestPlane(Positions, TrimValue, Planes, KeepValue)
            elif KeepValue.kind == 0x33:
                Updated[FaceIndex] = BestCyl(Positions, TrimValue, Cylinders, KeepValue)
        Current = Updated
    return tuple(Current)


# this definition exists because refinement must not pay for the tessellation snap
def PlaceRough(BrepValue: BrepData) -> dict[int, tuple[float, float, float]]:
    Usage, ArityTwo = CornerUsage(BrepValue)
    Positions = AssignCorners(BrepValue, Usage, ArityTwo)
    PlaceArcMut(BrepValue, Usage, ArityTwo, Positions)
    PlaceRestMut(BrepValue, Usage, Positions)
    return Positions


# this definition exists because a pooled cylinder needs a radial distance
def CylDist(
    Point: tuple[float, float, float],
    AxisValue: tuple[float, float, float],
    Center: tuple[float, float, float],
    Radius: float,
) -> float:
    Delta = [Point[Index] - Center[Index] for Index in range(3)]
    Along = sum(Delta[Index] * AxisValue[Index] for Index in range(3))
    Radial = math.sqrt(max(0.0, sum(Value * Value for Value in Delta) - Along**2))
    return abs(Radial - Radius)


# this definition exists because focused behavior needs one stable owner
def ParseBrep(Archive: CfvTwoArchive) -> BrepData:
    if not Archive.nested:
        raise ValueError("nested container is missing")
    Folder = Archive.nested[0]
    MainStream = Largest(Folder, "MainDataStream")
    SurfStream = Largest(Folder, "SurfacicReps")
    MainData = Archive.stream_bytes(MainStream, Folder)
    SurfData = Archive.stream_bytes(SurfStream, Folder)
    Surfaces = ParseSurfaces(SurfData)
    Roster = ParseRoster(SurfData)
    FbbOffset, FaceCount = FindFbb(MainData)
    EdgeOffset = FbbOffset + 8 * FaceCount
    for Width in (1, 2, 3):
        try:
            Edges, AfterEdges = ParseEdge(MainData, EdgeOffset, Width)
            Vertices, _ = ParseVert(MainData, AfterEdges)
            Trims = ParseTrims(MainData, FbbOffset, Width, FaceCount)
        except (IndexError, ValueError):
            continue
        if len(Trims) == FaceCount and len(Vertices) == len(Roster):
            Heuristic = len(Surfaces) != FaceCount
            FaceSurfaces = (
                list(AssignSurfaces(Surfaces, Trims, SurfData))
                if Heuristic
                else Surfaces
            )
            Provisional = BrepData(
                tuple(FaceSurfaces),
                Trims,
                Edges,
                Vertices,
                Roster,
                Width,
                (),
                Heuristic,
            )
            if Heuristic:
                Provisional = replace(
                    Provisional, surfaces=RefineMap(Provisional, Surfaces)
                )
            Radii = tuple(
                abs(Value.params[5])
                for Value in Provisional.surfaces
                if Value.kind == 0x33 and len(Value.params) >= 6
            )
            Tessellation = TessPoints(MainData, Radii) if Radii else ()
            return replace(Provisional, tessellation=Tessellation)
    raise ValueError("topology spine is unsupported")


# this definition exists because focused behavior needs one stable owner
def SurfaceLimits(BrepValue: BrepData, Faces: set[int]) -> tuple[
    list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    list[tuple[tuple[float, float, float], tuple[float, float, float], float]],
]:
    Planes: list[tuple[tuple[float, float, float], tuple[float, float, float]]] = []
    Cylinders: list[
        tuple[tuple[float, float, float], tuple[float, float, float], float]
    ] = []
    for FaceIndex in Faces:
        SurfaceValue = BrepValue.surfaces[FaceIndex]
        if SurfaceValue.kind == 0x32:
            Normal = BrepValue.trims[FaceIndex].vector
            if Normal is not None:
                Planes.append(
                    (
                        Normal,
                        (
                            SurfaceValue.bounds[0],
                            SurfaceValue.bounds[1],
                            SurfaceValue.bounds[2],
                        ),
                    )
                )
        elif SurfaceValue.kind == 0x33 and len(SurfaceValue.params) >= 6:
            Params = SurfaceValue.params
            Cylinders.append(
                (
                    AxisFromCarrier(Params),
                    (Params[0], Params[1], Params[2]),
                    abs(Params[5]),
                )
            )
    return Planes, Cylinders


# this definition exists because the least violating vertex is the safest fallback
def Violation(
    Point: tuple[float, float, float],
    Planes: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    Cylinders: list[
        tuple[tuple[float, float, float], tuple[float, float, float], float]
    ],
) -> float:
    Total = 0.0
    for Normal, Center in Planes:
        Total += abs(
            sum(
                Normal[IndexValue] * (Point[IndexValue] - Center[IndexValue])
                for IndexValue in range(3)
            )
        )
    for AxisValue, Center, Radius in Cylinders:
        Delta = [Point[IndexValue] - Center[IndexValue] for IndexValue in range(3)]
        Projection = sum(
            Delta[IndexValue] * AxisValue[IndexValue] for IndexValue in range(3)
        )
        Total += abs(
            math.sqrt(max(0.0, sum(Value * Value for Value in Delta) - Projection**2))
            - Radius
        )
    return Total


# this definition exists because the least violating vertex is the safest fallback
def NearestVertex(
    BrepValue: BrepData,
    Planes: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    Cylinders: list[
        tuple[tuple[float, float, float], tuple[float, float, float], float]
    ],
) -> tuple[float, float, float]:
    BestValue = BrepValue.vertices[0].point
    BestScore = Violation(BestValue, Planes, Cylinders)
    for VertexRow in BrepValue.vertices:
        Score = Violation(VertexRow.point, Planes, Cylinders)
        if Score < BestScore:
            BestValue = VertexRow.point
            BestScore = Score
    return BestValue


# this definition exists because focused behavior needs one stable owner
def IsSatisfied(
    Point: tuple[float, float, float],
    Planes: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    Cylinders: list[
        tuple[tuple[float, float, float], tuple[float, float, float], float]
    ],
) -> bool:
    for Normal, Center in Planes:
        if (
            abs(
                sum(
                    Normal[IndexValue] * (Point[IndexValue] - Center[IndexValue])
                    for IndexValue in range(3)
                )
            )
            >= 1e-3
        ):
            return False
    for AxisValue, Center, Radius in Cylinders:
        Delta = [Point[IndexValue] - Center[IndexValue] for IndexValue in range(3)]
        Projection = sum(
            Delta[IndexValue] * AxisValue[IndexValue] for IndexValue in range(3)
        )
        if (
            abs(
                math.sqrt(
                    max(0.0, sum(Value * Value for Value in Delta) - Projection**2)
                )
                - Radius
            )
            >= 1e-3
        ):
            return False
    return True


# this definition exists because focused behavior needs one stable owner
def ConeRadius(
    Normal: tuple[float, float, float],
    AxisValue: tuple[float, float, float],
    Origin: tuple[float, float, float],
    Center: tuple[float, float, float],
    HalfAngleValue: float,
) -> float | None:
    HalfAngle = abs(HalfAngleValue)
    if not 0.0 < HalfAngle < math.pi / 2.0:
        return None
    Alignment = abs(
        sum(Normal[IndexValue] * AxisValue[IndexValue] for IndexValue in range(3))
    )
    if abs(Alignment - 1.0) > 1e-3:
        return None
    Distance = abs(
        sum(
            Normal[IndexValue] * (Origin[IndexValue] - Center[IndexValue])
            for IndexValue in range(3)
        )
    )
    return Distance * math.tan(HalfAngle)


# this definition exists because focused behavior needs one stable owner
def IntersectCircle(
    BrepValue: BrepData, PairValue: tuple[int, int]
) -> tuple[tuple[float, float, float], tuple[float, float, float], float] | None:
    for PlaneIndex, OtherIndex in (PairValue, (PairValue[1], PairValue[0])):
        PlaneValue = BrepValue.surfaces[PlaneIndex]
        OtherValue = BrepValue.surfaces[OtherIndex]
        if PlaneValue.kind != 0x32:
            continue
        Normal = BrepValue.trims[PlaneIndex].vector
        if Normal is None or len(OtherValue.params) < 6:
            continue
        Center = (
            PlaneValue.bounds[0],
            PlaneValue.bounds[1],
            PlaneValue.bounds[2],
        )
        Params = OtherValue.params
        AxisValue = AxisFromCarrier(Params)
        Origin = (Params[0], Params[1], Params[2])
        if OtherValue.kind == 0x33:
            Radius = abs(Params[5])
        elif OtherValue.kind == 0x34:
            ConeValue = ConeRadius(Normal, AxisValue, Origin, Center, Params[5])
            if ConeValue is None:
                continue
            Radius = ConeValue
        else:
            continue
        if not math.isfinite(Radius) or Radius <= 0.0:
            continue
        Offset = sum(
            Normal[AxisValue] * (Origin[AxisValue] - Center[AxisValue])
            for AxisValue in range(3)
        )
        CircleCenter = (
            Origin[0] - Offset * Normal[0],
            Origin[1] - Offset * Normal[1],
            Origin[2] - Offset * Normal[2],
        )
        return CircleCenter, AxisValue, Radius
    return None


# this definition exists because focused behavior needs one stable owner
def ArcPoint(
    Center: tuple[float, float, float],
    AxisValue: tuple[float, float, float],
    Radius: float,
    Angle: float,
) -> tuple[float, float, float]:
    Reference = (
        Normalize((1.0, 0.0, 0.0))
        if abs(AxisValue[0]) < 0.9
        else Normalize((0.0, 1.0, 0.0))
    )
    Second = Normalize(
        (
            AxisValue[1] * Reference[2] - AxisValue[2] * Reference[1],
            AxisValue[2] * Reference[0] - AxisValue[0] * Reference[2],
            AxisValue[0] * Reference[1] - AxisValue[1] * Reference[0],
        )
    )
    First = Normalize(
        (
            Second[1] * AxisValue[2] - Second[2] * AxisValue[1],
            Second[2] * AxisValue[0] - Second[0] * AxisValue[2],
            Second[0] * AxisValue[1] - Second[1] * AxisValue[0],
        )
    )
    Cosine = math.cos(Angle)
    SineValue = math.sin(Angle)
    return (
        Center[0] + Radius * (First[0] * Cosine + Second[0] * SineValue),
        Center[1] + Radius * (First[1] * Cosine + Second[1] * SineValue),
        Center[2] + Radius * (First[2] * Cosine + Second[2] * SineValue),
    )


# this definition exists because focused behavior needs one stable owner
def LongestFloatRun(SourceData: bytes) -> list[float]:
    BestCount = 0
    BestStart = 0
    for Start in range(4):
        Cursor = Start
        while Cursor + 4 <= len(SourceData):
            Value = struct.unpack_from("<f", SourceData, Cursor)[0]
            if not (math.isfinite(Value) and abs(Value) < 1e4):
                Cursor += 4
                continue
            RunStart = Cursor
            Count = 0
            while Cursor + 4 <= len(SourceData):
                Value = struct.unpack_from("<f", SourceData, Cursor)[0]
                if not (math.isfinite(Value) and abs(Value) < 1e4):
                    break
                Cursor += 4
                Count += 1
            if Count > BestCount:
                BestCount = Count
                BestStart = RunStart
    if BestCount < 8:
        return []
    return [
        struct.unpack_from("<f", SourceData, BestStart + 4 * Index)[0]
        for Index in range(BestCount)
    ]


# this definition exists because focused behavior needs one stable owner
def TessPoints(
    SourceData: bytes, Radii: tuple[float, ...]
) -> tuple[tuple[float, float], ...]:
    Values = LongestFloatRun(SourceData)
    if not Values:
        return ()
    Points: list[tuple[float, float]] = []
    Cursor = 2
    while Cursor + 1 < len(Values):
        YValue = Values[Cursor]
        ZValue = Values[Cursor + 1]
        Radius = math.hypot(YValue, ZValue)
        if any(abs(Radius - Candidate) < 1e-2 for Candidate in Radii):
            Points.append((YValue, ZValue))
        if Cursor + 2 < len(Values) and abs(abs(ZValue) - Values[Cursor + 2]) < 2e-3:
            Cursor += 3
        else:
            Cursor += 2
    return tuple(Points)


# this definition exists because focused behavior needs one stable owner
def LocalFrame(
    BrepValue: BrepData,
) -> (
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    Candidates: dict[
        tuple[float, float, float], tuple[int, tuple[float, float, float]]
    ] = {}
    for SurfaceValue in BrepValue.surfaces:
        if SurfaceValue.kind != 0x33 or len(SurfaceValue.params) < 6:
            continue
        AxisValue = AxisFromCarrier(SurfaceValue.params)
        KeyValue = (
            round(AxisValue[0], 3),
            round(AxisValue[1], 3),
            round(AxisValue[2], 3),
        )
        Count, _ = Candidates.get(KeyValue, (0, (0.0, 0.0, 0.0)))
        Candidates[KeyValue] = (
            Count + 1,
            (SurfaceValue.params[0], SurfaceValue.params[1], SurfaceValue.params[2]),
        )
    if not Candidates:
        return None

    # this callback exists because the dominant carrier axis defines the local frame
    BestKey = max(Candidates, key=lambda Value: Candidates[Value][0])
    Origin = Candidates[BestKey][1]
    AxisValue = Normalize(BestKey)
    Reference = (
        Normalize((1.0, 0.0, 0.0))
        if abs(AxisValue[0]) < 0.9
        else Normalize((0.0, 1.0, 0.0))
    )
    Second = Normalize(
        (
            AxisValue[1] * Reference[2] - AxisValue[2] * Reference[1],
            AxisValue[2] * Reference[0] - AxisValue[0] * Reference[2],
            AxisValue[0] * Reference[1] - AxisValue[1] * Reference[0],
        )
    )
    First = Normalize(
        (
            Second[1] * AxisValue[2] - Second[2] * AxisValue[1],
            Second[2] * AxisValue[0] - Second[0] * AxisValue[2],
            Second[0] * AxisValue[1] - Second[1] * AxisValue[0],
        )
    )
    return First, Second, AxisValue, Origin


# this definition exists because a decoded tessellation region can cover part of a ring
def TessRing(
    BrepValue: BrepData,
) -> list[tuple[float, float]]:
    Groups: dict[float, list[float]] = {}
    for FirstPoint, SecondPoint in BrepValue.tessellation:
        Radius = math.hypot(FirstPoint, SecondPoint)
        if Radius <= 1e-9:
            continue
        KeyValue = round(Radius, 3)
        Groups.setdefault(KeyValue, []).append(math.atan2(SecondPoint, FirstPoint))
    RingValues: list[tuple[float, float]] = []
    for Radius, Angles in Groups.items():
        Unique = sorted({round(Angle, 4) for Angle in Angles})
        if len(Unique) < 3:
            continue
        StepValue = min(
            Unique[Index + 1] - Unique[Index] for Index in range(len(Unique) - 1)
        )
        if StepValue <= 1e-6:
            continue
        BaseValue = Unique[0]
        if any(
            abs(
                (Angle - BaseValue) / StepValue - round((Angle - BaseValue) / StepValue)
            )
            > 1e-3
            for Angle in Unique
        ):
            continue
        Count = int(round(2.0 * math.pi / StepValue))
        if Count < len(Unique) or Count > 360:
            continue
        for Index in range(Count):
            Angle = BaseValue + Index * StepValue
            RingValues.append((Radius * math.cos(Angle), Radius * math.sin(Angle)))
    return RingValues


# this definition exists because focused behavior needs one stable owner
def SnapToTessMut(
    BrepValue: BrepData,
    Positions: dict[int, tuple[float, float, float]],
    Usage: dict[int, set[int]],
) -> None:
    if not BrepValue.tessellation:
        return
    Frame = LocalFrame(BrepValue)
    if Frame is None:
        return
    First, Second, AxisValue, Origin = Frame
    Candidates = list(BrepValue.tessellation) + TessRing(BrepValue)
    for Handle, Point in Positions.items():
        Delta = (
            Point[0] - Origin[0],
            Point[1] - Origin[1],
            Point[2] - Origin[2],
        )
        Along = sum(Delta[Index] * AxisValue[Index] for Index in range(3))
        FirstValue = sum(Delta[Index] * First[Index] for Index in range(3))
        SecondValue = sum(Delta[Index] * Second[Index] for Index in range(3))
        Radius = math.hypot(FirstValue, SecondValue)
        Nearby = [
            (FirstPoint, SecondPoint)
            for FirstPoint, SecondPoint in Candidates
            if abs(math.hypot(FirstPoint, SecondPoint) - Radius) < 1e-2
        ]
        if not Nearby:
            continue

        # this callback exists because the nearest tessellation point is the snap target
        BestValue = min(
            Nearby,
            key=lambda Value: math.hypot(Value[0] - FirstValue, Value[1] - SecondValue),
        )
        Snapped = (
            Origin[0]
            + BestValue[0] * First[0]
            + BestValue[1] * Second[0]
            + Along * AxisValue[0],
            Origin[1]
            + BestValue[0] * First[1]
            + BestValue[1] * Second[1]
            + Along * AxisValue[1],
            Origin[2]
            + BestValue[0] * First[2]
            + BestValue[1] * Second[2]
            + Along * AxisValue[2],
        )
        Planes, Cylinders = SurfaceLimits(BrepValue, Usage[Handle])
        if (
            Violation(Snapped, Planes, Cylinders)
            > Violation(Point, Planes, Cylinders) + 1e-6
        ):
            continue
        Positions[Handle] = Snapped


# this definition exists because focused behavior needs one stable owner
def CornerUsage(
    BrepValue: BrepData,
) -> tuple[dict[int, set[int]], list[int]]:
    Usage: dict[int, set[int]] = {}
    for FaceIndex, TrimValue in enumerate(BrepValue.trims):
        for Handle in set(TrimValue.handles):
            Usage.setdefault(Handle, set()).add(FaceIndex)
    ArityTwo = sorted(
        {
            Handle
            for EdgeValue in BrepValue.edges
            if EdgeValue.arity == 2
            for Handle in EdgeValue.handles
        }
    )
    return Usage, ArityTwo


# this definition exists because focused behavior needs one stable owner
def AssignCorners(
    BrepValue: BrepData,
    Usage: dict[int, set[int]],
    ArityTwo: list[int],
) -> dict[int, tuple[float, float, float]]:
    Candidates = {
        Handle: [
            Index
            for Index, VertexRow in enumerate(BrepValue.vertices)
            if IsSatisfied(VertexRow.point, *SurfaceLimits(BrepValue, Usage[Handle]))
        ]
        for Handle in ArityTwo
    }
    Assign: dict[int, int] = {}

    # this definition exists because greedy matching leaves valid corners unmatched
    def CanMatchMut(Handle: int, SeenValues: set[int]) -> bool:
        for Index in Candidates[Handle]:
            if Index in SeenValues:
                continue
            SeenValues.add(Index)
            if Index not in Assign or CanMatchMut(Assign[Index], SeenValues):
                Assign[Index] = Handle
                return True
        return False

    # this callback exists because the most constrained handles must be tried first
    for Handle in sorted(ArityTwo, key=lambda Value: len(Candidates[Value])):
        _ = CanMatchMut(Handle, set())
    return {Handle: BrepValue.vertices[Index].point for Index, Handle in Assign.items()}


# this definition exists because arc handles must follow the stored edge order
def ArcOrder(BrepValue: BrepData, Handles: list[int]) -> list[int] | None:
    HandleSet = set(Handles)
    for EdgeValue in BrepValue.edges:
        if EdgeValue.arity < 3:
            continue
        if not HandleSet.issubset(EdgeValue.handles):
            continue
        return list(EdgeValue.handles)
    return None


# this definition exists because arc handles must follow the stored edge order
def ArcHandles(
    BrepValue: BrepData,
    Handles: list[int],
    EndValues: list[int],
    Positions: dict[int, tuple[float, float, float]],
) -> tuple[list[int], list[int]]:
    EdgeOrder = ArcOrder(BrepValue, Handles)
    if EdgeOrder is None:
        return (EndValues, Handles)
    if EdgeOrder[0] in Positions and EdgeOrder[-1] in Positions:
        return ([EdgeOrder[0], EdgeOrder[-1]], EdgeOrder[1:-1])
    EdgeValues = [Handle for Handle in EdgeOrder if Handle in Handles]
    if len(EdgeValues) == len(Handles):
        return (EndValues, EdgeValues)
    return (EndValues, Handles)


# this definition exists because focused behavior needs one stable owner
def PlaceArcMut(
    BrepValue: BrepData,
    Usage: dict[int, set[int]],
    ArityTwo: list[int],
    Positions: dict[int, tuple[float, float, float]],
) -> None:
    Pairs: dict[tuple[int, int], list[int]] = defaultdict(list)
    for Handle in sorted(Usage):
        if len(Usage[Handle]) == 2:
            Faces = sorted(Usage[Handle])
            Pairs[(Faces[0], Faces[1])].append(Handle)
    for PairValue, Handles in Pairs.items():
        Circle = IntersectCircle(BrepValue, PairValue)
        if Circle is None:
            continue
        Center, AxisValue, Radius = Circle
        EndValues = [
            Handle
            for Handle in ArityTwo
            if Handle in Positions
            and abs(math.dist(Positions[Handle], Center) - Radius) < 1e-3
        ]
        if len(EndValues) != 2:
            continue
        EndValues, Handles = ArcHandles(BrepValue, Handles, EndValues, Positions)
        Reference = (
            Normalize((1.0, 0.0, 0.0))
            if abs(AxisValue[0]) < 0.9
            else Normalize((0.0, 1.0, 0.0))
        )
        Second = Normalize(
            (
                AxisValue[1] * Reference[2] - AxisValue[2] * Reference[1],
                AxisValue[2] * Reference[0] - AxisValue[0] * Reference[2],
                AxisValue[0] * Reference[1] - AxisValue[1] * Reference[0],
            )
        )
        First = Normalize(
            (
                Second[1] * AxisValue[2] - Second[2] * AxisValue[1],
                Second[2] * AxisValue[0] - Second[0] * AxisValue[2],
                Second[0] * AxisValue[1] - Second[1] * AxisValue[0],
            )
        )

        # this definition exists because arc handles need an angle about the circle axis
        def Angle(Point: tuple[float, float, float]) -> float:
            Delta = (
                Point[0] - Center[0],
                Point[1] - Center[1],
                Point[2] - Center[2],
            )
            return math.atan2(
                sum(Delta[AxisValue] * Second[AxisValue] for AxisValue in range(3)),
                sum(Delta[AxisValue] * First[AxisValue] for AxisValue in range(3)),
            )

        Start = Angle(Positions[EndValues[0]])
        Delta = Angle(Positions[EndValues[1]]) - Start
        while Delta > math.pi:
            Delta -= 2.0 * math.pi
        while Delta < -math.pi:
            Delta += 2.0 * math.pi
        StepValue = len(Handles) + 1
        for Index, Handle in enumerate(Handles):
            Positions[Handle] = ArcPoint(
                Center, AxisValue, Radius, Start + Delta * (Index + 1) / StepValue
            )


# this definition exists because focused behavior needs one stable owner
def PlaceRestMut(
    BrepValue: BrepData,
    Usage: dict[int, set[int]],
    Positions: dict[int, tuple[float, float, float]],
) -> None:
    for Handle in sorted(Usage):
        if Handle in Positions:
            continue
        Planes, Cylinders = SurfaceLimits(BrepValue, Usage[Handle])
        BestValue = None
        BestDistance = None
        for VertexRow in BrepValue.vertices:
            if not IsSatisfied(VertexRow.point, Planes, Cylinders):
                continue
            Distance = sum(
                (VertexRow.point[AxisValue] - BrepValue.vertices[0].point[AxisValue])
                ** 2
                for AxisValue in range(3)
            )
            if BestDistance is None or Distance < BestDistance:
                BestValue = VertexRow.point
                BestDistance = Distance
        Positions[Handle] = (
            BestValue
            if BestValue is not None
            else NearestVertex(BrepValue, Planes, Cylinders)
        )


# this definition exists because focused behavior needs one stable owner
def CornerPositions(
    BrepValue: BrepData,
) -> dict[int, tuple[float, float, float]]:
    Usage, ArityTwo = CornerUsage(BrepValue)
    Positions = AssignCorners(BrepValue, Usage, ArityTwo)
    PlaceArcMut(BrepValue, Usage, ArityTwo, Positions)
    PlaceRestMut(BrepValue, Usage, Positions)
    SnapToTessMut(BrepValue, Positions, Usage)
    return Positions


# this definition exists because focused behavior needs one stable owner
def BuildVertices(
    BrepValue: BrepData,
) -> tuple[tuple[BrepVertex, ...], dict[int, str]]:
    if not BrepValue.vertices:
        raise ValueError("vertex table is empty")
    Positions = CornerPositions(BrepValue)
    Handles = sorted(Positions)
    Vertices = tuple(
        BrepVertex(f"catia:vertex:{Index + 1}", Vector(Positions[Handle]))
        for Index, Handle in enumerate(Handles)
    )
    VertexByHandle = {
        Handle: f"catia:vertex:{Index + 1}" for Index, Handle in enumerate(Handles)
    }
    return Vertices, VertexByHandle


# this definition exists because focused behavior needs one stable owner
def ArcCircles(
    BrepValue: BrepData,
) -> dict[int, tuple[tuple[float, float, float], tuple[float, float, float], float]]:
    Usage: dict[int, set[int]] = {}
    for FaceIndex, TrimValue in enumerate(BrepValue.trims):
        for Handle in set(TrimValue.handles):
            Usage.setdefault(Handle, set()).add(FaceIndex)
    Pairs: dict[tuple[int, int], list[int]] = defaultdict(list)
    for Handle in sorted(Usage):
        if len(Usage[Handle]) == 2:
            Faces = sorted(Usage[Handle])
            Pairs[(Faces[0], Faces[1])].append(Handle)
    Circles: dict[
        int, tuple[tuple[float, float, float], tuple[float, float, float], float]
    ] = {}
    for PairValue, Handles in Pairs.items():
        Circle = IntersectCircle(BrepValue, PairValue)
        if Circle is None:
            continue
        for Handle in Handles:
            Circles[Handle] = Circle
    return Circles


# this definition exists because focused behavior needs one stable owner
def BuildEdge(
    HandlePair: tuple[int, int],
    VertexByHandle: dict[int, str],
    VertexById: dict[str, BrepVertex],
    CurveCount: int,
    Circle: (
        tuple[tuple[float, float, float], tuple[float, float, float], float] | None
    ) = None,
) -> tuple[LineCurve | CircleCurve, BrepEdge]:
    StartId = VertexByHandle[HandlePair[0]]
    EndId = VertexByHandle[HandlePair[1]]
    StartPoint = VertexById[StartId].point
    EndPoint = VertexById[EndId].point
    CurveId = f"catia:curve:{CurveCount + 1}"
    EdgeId = f"catia:edge:{CurveCount + 1}"
    if Circle is not None:
        Center, AxisValue, Radius = Circle
        StartDelta = (
            StartPoint.x - Center[0],
            StartPoint.y - Center[1],
            StartPoint.z - Center[2],
        )
        EndDelta = (
            EndPoint.x - Center[0],
            EndPoint.y - Center[1],
            EndPoint.z - Center[2],
        )
        StartLength = math.sqrt(sum(Value * Value for Value in StartDelta))
        EndLength = math.sqrt(sum(Value * Value for Value in EndDelta))
        if StartLength > 1e-9 and EndLength > 1e-9:
            Cosine = sum(
                StartDelta[AxisValue] * EndDelta[AxisValue] for AxisValue in range(3)
            ) / (StartLength * EndLength)
            Angle = math.acos(max(-1.0, min(1.0, Cosine)))
            if 1e-9 < Angle < math.pi - 1e-9:
                CurveValue = CircleCurve(
                    CurveId,
                    Vector(Center),
                    Vector(AxisValue),
                    Vector(
                        (
                            StartDelta[0] / StartLength,
                            StartDelta[1] / StartLength,
                            StartDelta[2] / StartLength,
                        )
                    ),
                    Radius,
                )
                return CurveValue, BrepEdge(EdgeId, StartId, EndId, CurveId, 0.0, Angle)
    Direction = Normalize(
        (
            EndPoint.x - StartPoint.x,
            EndPoint.y - StartPoint.y,
            EndPoint.z - StartPoint.z,
        )
    )
    LineValue: LineCurve | CircleCurve = LineCurve(
        CurveId, StartPoint, Vector(Direction)
    )
    Length = math.dist(
        (StartPoint.x, StartPoint.y, StartPoint.z),
        (EndPoint.x, EndPoint.y, EndPoint.z),
    )
    return LineValue, BrepEdge(EdgeId, StartId, EndId, CurveId, 0.0, Length)


# this definition exists because focused behavior needs one stable owner
def CycleArea(
    Cycle: tuple[int, ...],
    VertexByHandle: dict[int, str],
    VertexById: dict[str, BrepVertex],
) -> float:
    Points = [VertexById[VertexByHandle[Handle]].point for Handle in Cycle]
    Total = [0.0, 0.0, 0.0]
    for Index, Point in enumerate(Points):
        NextPoint = Points[(Index + 1) % len(Points)]
        Total[0] += Point.y * NextPoint.z - Point.z * NextPoint.y
        Total[1] += Point.z * NextPoint.x - Point.x * NextPoint.z
        Total[2] += Point.x * NextPoint.y - Point.y * NextPoint.x
    return 0.5 * math.sqrt(sum(Value * Value for Value in Total))


# this definition exists because focused behavior needs one stable owner
def BuildCycleMut(
    Cycle: tuple[int, ...],
    VertexByHandle: dict[int, str],
    VertexById: dict[str, BrepVertex],
    EdgeByPair: dict[tuple[int, int], str],
    CurveCount: int,
    CoedgeCount: int,
    Circles: dict[
        int, tuple[tuple[float, float, float], tuple[float, float, float], float]
    ],
    Curves: list[LineCurve | CircleCurve],
    Edges: list[BrepEdge],
    Coedges: list[BrepCoedge],
) -> list[str]:
    CoedgeIds: list[str] = []
    for Position, StartHandle in enumerate(Cycle):
        EndHandle = Cycle[(Position + 1) % len(Cycle)]
        HandlePair = (min(StartHandle, EndHandle), max(StartHandle, EndHandle))
        EdgeId = EdgeByPair.get(HandlePair)
        if EdgeId is None:
            Circle = Circles.get(StartHandle) or Circles.get(EndHandle)
            if Circle is not None:
                Center, _, Radius = Circle
                for Handle in HandlePair:
                    Point = VertexById[VertexByHandle[Handle]].point
                    if (
                        abs(math.dist((Point.x, Point.y, Point.z), Center) - Radius)
                        > 1e-3
                    ):
                        Circle = None
                        break
            CurveValue, EdgeValue = BuildEdge(
                HandlePair,
                VertexByHandle,
                VertexById,
                CurveCount + len(Curves),
                Circle,
            )
            EdgeId = EdgeValue.id
            EdgeByPair[HandlePair] = EdgeId
            Curves.append(CurveValue)
            Edges.append(EdgeValue)
        CoedgeId = f"catia:coedge:{CoedgeCount + len(Coedges) + 1}"
        Coedges.append(BrepCoedge(CoedgeId, EdgeId, reversed=StartHandle > EndHandle))
        CoedgeIds.append(CoedgeId)
    return CoedgeIds


# this definition exists because focused behavior needs one stable owner
def BuildFaceMut(
    FaceIndex: int,
    SurfaceValue: SurfaceRec,
    TrimValue: TrimRec,
    VertexByHandle: dict[int, str],
    VertexById: dict[str, BrepVertex],
    EdgeByPair: dict[tuple[int, int], str],
    CurveCount: int,
    EdgeCount: int,
    CoedgeCount: int,
    Circles: dict[
        int, tuple[tuple[float, float, float], tuple[float, float, float], float]
    ],
) -> FaceBuild:
    Curves: list[LineCurve | CircleCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []
    Loops: list[BrepLoop] = []
    LoopIds: list[str] = []
    Cycles = Boundary(TrimValue)
    Areas = [CycleArea(Cycle, VertexByHandle, VertexById) for Cycle in Cycles]

    # this callback exists because the outer loop is the cycle with the largest area
    OuterIndex = (
        max(range(len(Cycles)), key=lambda Value: Areas[Value]) if Cycles else -1
    )
    for CycleIndex, Cycle in enumerate(Cycles, start=1):
        CoedgeIds = BuildCycleMut(
            Cycle,
            VertexByHandle,
            VertexById,
            EdgeByPair,
            CurveCount,
            CoedgeCount,
            Circles,
            Curves,
            Edges,
            Coedges,
        )
        LoopId = f"catia:loop:{FaceIndex}:{CycleIndex}"
        Loops.append(
            BrepLoop(LoopId, tuple(CoedgeIds), outer=CycleIndex - 1 == OuterIndex)
        )
        LoopIds.append(LoopId)
    FaceValue = BrepFace(
        f"catia:face:{FaceIndex}",
        f"catia:surface:{FaceIndex}",
        tuple(LoopIds),
        same_sense=SurfaceValue.sign >= 0,
    )
    return FaceBuild(
        tuple(Curves), tuple(Edges), tuple(Coedges), tuple(Loops), FaceValue
    )


# this definition exists because focused behavior needs one stable owner
def BuildBrep(BrepValue: BrepData) -> BrepModel:
    Vertices, VertexByHandle = BuildVertices(BrepValue)
    VertexById = {VertexValue.id: VertexValue for VertexValue in Vertices}
    Circles = ArcCircles(BrepValue)
    Curves: list[LineCurve | CircleCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []
    Loops: list[BrepLoop] = []
    Faces: list[BrepFace] = []
    Surfaces: list[BrepSurface] = []
    EdgeByPair: dict[tuple[int, int], str] = {}
    for FaceIndex, (SurfaceValue, TrimValue) in enumerate(
        zip(BrepValue.surfaces, BrepValue.trims), start=1
    ):
        Surfaces.append(MakeSurf(SurfaceValue, FaceIndex, TrimValue.vector))
        FaceResult = BuildFaceMut(
            FaceIndex,
            SurfaceValue,
            TrimValue,
            VertexByHandle,
            VertexById,
            EdgeByPair,
            len(Curves),
            len(Edges),
            len(Coedges),
            Circles,
        )
        Curves.extend(FaceResult.curves)
        Edges.extend(FaceResult.edges)
        Coedges.extend(FaceResult.coedges)
        Loops.extend(FaceResult.loops)
        Faces.append(FaceResult.face)
    FaceUses = tuple(
        BrepFaceUse(f"catia:face-use:{Index}", FaceValue.id)
        for Index, FaceValue in enumerate(Faces, start=1)
    )
    Shell = BrepShell(
        "catia:shell:1", tuple(Value.id for Value in FaceUses), closed=True
    )
    ShellUse = BrepShellUse("catia:shell-use:1", Shell.id)
    Region = BrepRegion("catia:region:1", (ShellUse.id,), solid=True)
    BodyValue = BrepBody(KBodyId, (Region.id,), design_body_id=KBodyId)
    return BrepModel(
        curves=tuple(Curves),
        surfaces=tuple(Surfaces),
        vertices=Vertices,
        edges=tuple(Edges),
        coedges=tuple(Coedges),
        loops=tuple(Loops),
        faces=tuple(Faces),
        face_uses=FaceUses,
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(BodyValue,),
    )


# this definition exists because focused behavior needs one stable owner
def DecodeTess(Archive: CfvTwoArchive) -> tuple[tuple[float, float], ...]:
    if not Archive.nested:
        return ()
    Folder = Archive.nested[0]
    MainData = Archive.stream_bytes(Largest(Folder, "MainDataStream"), Folder)
    SurfData = Archive.stream_bytes(Largest(Folder, "SurfacicReps"), Folder)
    Radii = tuple(
        abs(Value.params[5])
        for Value in ParseSurfaces(SurfData)
        if Value.kind == 0x33 and len(Value.params) >= 6
    )
    if not Radii:
        return ()
    return TessPoints(MainData, Radii)


# this definition exists because focused behavior needs one stable owner
def DecodeBrep(
    Archive: CfvTwoArchive,
) -> tuple[BrepModel | None, tuple[Diagnostic, ...]]:
    try:
        BrepValue = ParseBrep(Archive)
        Model = BuildBrep(BrepValue)
    except (IndexError, TypeError, ValueError) as ErrorInfo:
        return None, (
            Diagnostic(
                "catia.brep.native_decode_failed",
                f"Native CATIA B-rep decoding failed: {ErrorInfo}",
                Severity.WARNING,
            ),
        )
    Errors = Model.validate(frozenset({KBodyId}))
    if Errors:
        return None, (
            Diagnostic(
                "catia.brep.native_validation_failed",
                f"Native CATIA B-rep validation failed: {Errors[0]}",
                Severity.WARNING,
            ),
        )
    Diagnostics = [
        Diagnostic(
            "catia.brep.native_decoded",
            "CATIA tessellation-derived topology and surface bounds were decoded.",
            Severity.INFO,
            attributes={
                "face_count": len(Model.faces),
                "edge_count": len(Model.edges),
                "vertex_count": len(Model.vertices),
                "surface_count": len(Model.surfaces),
            },
        )
    ]
    if BrepValue.heuristic:
        Diagnostics.append(
            Diagnostic(
                "catia.brep.native_surface_map_heuristic",
                "The face-to-surface map was inferred from edge circles and trim normals because the stored map was not located; geometry is approximate for this part.",
                Severity.WARNING,
            )
        )
    return Model, tuple(Diagnostics)
