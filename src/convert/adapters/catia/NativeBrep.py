from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
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
    return max(Matches, key=lambda Stream: Stream.logical_length)


# this definition exists because focused behavior needs one stable owner
def ParseSurfaces(SourceData: bytes) -> list[SurfaceRec]:
    Surfaces: list[SurfaceRec] = []
    End = -1
    for Marker in range(len(SourceData) - 5):
        if SourceData[Marker : Marker + 2] != b"\x00\x33":
            continue
        if SourceData[Marker + 2] not in KSurfaceKinds:
            continue
        Offset = Marker - 2
        if Offset < End:
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
        End = NextOffset
    return Surfaces


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
    if len(Surfaces) != FaceCount:
        raise ValueError(
            "surface count does not match the face count ("
            + f"{len(Surfaces)} surfaces, {FaceCount} faces)"
        )
    EdgeOffset = FbbOffset + 8 * FaceCount
    for Width in (1, 2, 3):
        try:
            Edges, AfterEdges = ParseEdge(MainData, EdgeOffset, Width)
            Vertices, _ = ParseVert(MainData, AfterEdges)
            Trims = ParseTrims(MainData, FbbOffset, Width, FaceCount)
        except (IndexError, ValueError):
            continue
        if len(Trims) == FaceCount and len(Vertices) == len(Roster):
            Radii = tuple(
                abs(Value.params[5])
                for Value in Surfaces
                if Value.kind == 0x33 and len(Value.params) >= 6
            )
            Tessellation = TessellationPoints(MainData, Radii) if Radii else ()
            return BrepData(
                tuple(Surfaces),
                Trims,
                Edges,
                Vertices,
                Roster,
                Width,
                Tessellation,
            )
    raise ValueError("topology spine is unsupported")


# this definition exists because focused behavior needs one stable owner
def SurfaceConstraints(BrepValue: BrepData, Faces: set[int]) -> tuple[
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


# this definition exists because focused behavior needs one stable owner
def Satisfies(
    Point: tuple[float, float, float],
    Planes: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    Cylinders: list[
        tuple[tuple[float, float, float], tuple[float, float, float], float]
    ],
) -> bool:
    for Normal, Center in Planes:
        if (
            abs(sum(Normal[Axis] * (Point[Axis] - Center[Axis]) for Axis in range(3)))
            >= 1e-3
        ):
            return False
    for AxisValue, Center, Radius in Cylinders:
        Delta = [Point[Axis] - Center[Axis] for Axis in range(3)]
        Projection = sum(Delta[Axis] * AxisValue[Axis] for Axis in range(3))
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
def IntersectionCircle(
    BrepValue: BrepData, Pair: tuple[int, int]
) -> tuple[tuple[float, float, float], tuple[float, float, float], float] | None:
    for PlaneIndex, OtherIndex in (Pair, (Pair[1], Pair[0])):
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
            HalfAngle = abs(Params[5])
            if not 0.0 < HalfAngle < math.pi / 2.0:
                continue
            Alignment = abs(sum(Normal[Axis] * AxisValue[Axis] for Axis in range(3)))
            if abs(Alignment - 1.0) > 1e-3:
                continue
            Distance = abs(
                sum(Normal[Axis] * (Origin[Axis] - Center[Axis]) for Axis in range(3))
            )
            Radius = Distance * math.tan(HalfAngle)
        else:
            continue
        if not math.isfinite(Radius) or Radius <= 0.0:
            continue
        Offset = sum(Normal[Axis] * (Origin[Axis] - Center[Axis]) for Axis in range(3))
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
    Sine = math.sin(Angle)
    return (
        Center[0] + Radius * (First[0] * Cosine + Second[0] * Sine),
        Center[1] + Radius * (First[1] * Cosine + Second[1] * Sine),
        Center[2] + Radius * (First[2] * Cosine + Second[2] * Sine),
    )


# this definition exists because focused behavior needs one stable owner
def TessellationPoints(
    SourceData: bytes, Radii: tuple[float, ...]
) -> tuple[tuple[float, float], ...]:
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
        return ()
    Values = [
        struct.unpack_from("<f", SourceData, BestStart + 4 * Index)[0]
        for Index in range(BestCount)
    ]
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
def CornerPositions(
    BrepValue: BrepData,
) -> dict[int, tuple[float, float, float]]:
    Usage: dict[int, set[int]] = {}
    for FaceIndex, TrimValue in enumerate(BrepValue.trims):
        for Handle in set(TrimValue.handles):
            Usage.setdefault(Handle, set()).add(FaceIndex)
    Arity2 = sorted(
        {
            Handle
            for EdgeValue in BrepValue.edges
            if EdgeValue.arity == 2
            for Handle in EdgeValue.handles
        }
    )
    Candidates = {
        Handle: [
            Index
            for Index, VertexRow in enumerate(BrepValue.vertices)
            if Satisfies(VertexRow.point, *SurfaceConstraints(BrepValue, Usage[Handle]))
        ]
        for Handle in Arity2
    }
    Assign: dict[int, int] = {}
    Used: set[int] = set()
    for Handle in sorted(Arity2, key=lambda Value: len(Candidates[Value])):
        for Index in Candidates[Handle]:
            if Index not in Used:
                Assign[Handle] = Index
                Used.add(Index)
                break
    Positions: dict[int, tuple[float, float, float]] = {
        Handle: BrepValue.vertices[Index].point for Handle, Index in Assign.items()
    }
    Pairs: dict[tuple[int, int], list[int]] = defaultdict(list)
    for Handle in sorted(Usage):
        if len(Usage[Handle]) == 2:
            Faces = sorted(Usage[Handle])
            Pairs[(Faces[0], Faces[1])].append(Handle)
    for Pair, Handles in Pairs.items():
        Circle = IntersectionCircle(BrepValue, Pair)
        if Circle is None:
            continue
        Center, AxisValue, Radius = Circle
        Ends = [
            Handle
            for Handle in Arity2
            if Handle in Positions
            and abs(math.dist(Positions[Handle], Center) - Radius) < 1e-3
        ]
        if len(Ends) != 2:
            continue
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

        def Angle(Point: tuple[float, float, float]) -> float:
            Delta = (
                Point[0] - Center[0],
                Point[1] - Center[1],
                Point[2] - Center[2],
            )
            return math.atan2(
                sum(Delta[Axis] * Second[Axis] for Axis in range(3)),
                sum(Delta[Axis] * First[Axis] for Axis in range(3)),
            )

        Start = Angle(Positions[Ends[0]])
        Delta = Angle(Positions[Ends[1]]) - Start
        while Delta > math.pi:
            Delta -= 2.0 * math.pi
        while Delta < -math.pi:
            Delta += 2.0 * math.pi
        Step = len(Handles) + 1
        for Index, Handle in enumerate(Handles):
            Positions[Handle] = ArcPoint(
                Center, AxisValue, Radius, Start + Delta * (Index + 1) / Step
            )
    for Handle in sorted(Usage):
        if Handle in Positions:
            continue
        Planes, Cylinders = SurfaceConstraints(BrepValue, Usage[Handle])
        Best = None
        BestDistance = None
        for VertexRow in BrepValue.vertices:
            if not Satisfies(VertexRow.point, Planes, Cylinders):
                continue
            Distance = sum(
                (VertexRow.point[Axis] - BrepValue.vertices[0].point[Axis]) ** 2
                for Axis in range(3)
            )
            if BestDistance is None or Distance < BestDistance:
                Best = VertexRow.point
                BestDistance = Distance
        Positions[Handle] = Best if Best is not None else BrepValue.vertices[0].point
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
    for Pair, Handles in Pairs.items():
        Circle = IntersectionCircle(BrepValue, Pair)
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
            Cosine = sum(StartDelta[Axis] * EndDelta[Axis] for Axis in range(3)) / (
                StartLength * EndLength
            )
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
    OuterIndex = (
        max(range(len(Cycles)), key=lambda Value: Areas[Value]) if Cycles else -1
    )
    for CycleIndex, Cycle in enumerate(Cycles, start=1):
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
            Coedges.append(
                BrepCoedge(CoedgeId, EdgeId, reversed=StartHandle > EndHandle)
            )
            CoedgeIds.append(CoedgeId)
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
def DecodeTessellation(Archive: CfvTwoArchive) -> tuple[tuple[float, float], ...]:
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
    return TessellationPoints(MainData, Radii)


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
    return Model, (
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
        ),
    )
