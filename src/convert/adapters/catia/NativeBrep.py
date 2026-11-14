from __future__ import annotations

from dataclasses import dataclass
import math

from convert.adapters.catia.Container import CfvTwoArchive, CfvTwoFolder, CfvTwoStream
from convert.adapters.catia.NativeSurface import MakeSurf, ParseSurf, SurfaceRec
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


# this definition exists because focused behavior needs one stable owner
@dataclass(frozen=True, slots=True)
class FaceBuild:
    curves: tuple[LineCurve, ...]
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
def ParseBrep(Archive: CfvTwoArchive) -> BrepData:
    if not Archive.nested:
        raise ValueError("nested container is missing")
    Folder = Archive.nested[0]
    MainStream = Largest(Folder, "MainDataStream")
    SurfStream = Largest(Folder, "SurfacicReps")
    MainData = Archive.stream_bytes(MainStream, Folder)
    SurfData = Archive.stream_bytes(SurfStream, Folder)
    Surfaces: list[SurfaceRec] = []
    Offset = 17
    while Offset + 5 <= len(SurfData):
        try:
            SurfaceValue, NextOffset = ParseSurf(SurfData, Offset)
        except (IndexError, ValueError):
            break
        Surfaces.append(SurfaceValue)
        Offset = NextOffset
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
            return BrepData(tuple(Surfaces), Trims, Edges, Vertices, Roster, Width)
    raise ValueError("topology spine is unsupported")


# this definition exists because focused behavior needs one stable owner
def BuildVertices(
    BrepValue: BrepData,
) -> tuple[tuple[BrepVertex, ...], dict[int, str]]:
    if not BrepValue.vertices:
        raise ValueError("vertex table is empty")
    Handles = sorted(
        {Handle for TrimValue in BrepValue.trims for Handle in TrimValue.handles}
    )
    Vertices = tuple(
        BrepVertex(f"catia:vertex:{Index + 1}", Vector(VertexRow.point))
        for Index, VertexRow in enumerate(BrepValue.vertices)
    )
    VertexByHandle = {
        Handle: f"catia:vertex:{(Handle % len(BrepValue.vertices)) + 1}"
        for Handle in Handles
    }
    return Vertices, VertexByHandle


# this definition exists because focused behavior needs one stable owner
def BuildEdge(
    HandlePair: tuple[int, int],
    VertexByHandle: dict[int, str],
    VertexById: dict[str, BrepVertex],
    CurveCount: int,
) -> tuple[LineCurve, BrepEdge]:
    StartId = VertexByHandle[HandlePair[0]]
    EndId = VertexByHandle[HandlePair[1]]
    StartPoint = VertexById[StartId].point
    EndPoint = VertexById[EndId].point
    Direction = Normalize(
        (
            EndPoint.x - StartPoint.x,
            EndPoint.y - StartPoint.y,
            EndPoint.z - StartPoint.z,
        )
    )
    CurveId = f"catia:curve:{CurveCount + 1}"
    CurveValue = LineCurve(CurveId, StartPoint, Vector(Direction))
    Length = math.dist(
        (StartPoint.x, StartPoint.y, StartPoint.z),
        (EndPoint.x, EndPoint.y, EndPoint.z),
    )
    EdgeId = f"catia:edge:{CurveCount + 1}"
    return CurveValue, BrepEdge(EdgeId, StartId, EndId, CurveId, 0.0, Length)


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
) -> FaceBuild:
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []
    Loops: list[BrepLoop] = []
    LoopIds: list[str] = []
    for CycleIndex, Cycle in enumerate(Boundary(TrimValue), start=1):
        CoedgeIds: list[str] = []
        for Position, StartHandle in enumerate(Cycle):
            EndHandle = Cycle[(Position + 1) % len(Cycle)]
            HandlePair = (min(StartHandle, EndHandle), max(StartHandle, EndHandle))
            EdgeId = EdgeByPair.get(HandlePair)
            if EdgeId is None:
                CurveValue, EdgeValue = BuildEdge(
                    HandlePair,
                    VertexByHandle,
                    VertexById,
                    CurveCount + len(Curves),
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
        Loops.append(BrepLoop(LoopId, tuple(CoedgeIds), outer=CycleIndex == 1))
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
    Curves: list[LineCurve] = []
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
            "Native CATIA B-rep topology and analytic surfaces were decoded.",
            Severity.INFO,
            attributes={
                "face_count": len(Model.faces),
                "edge_count": len(Model.edges),
                "vertex_count": len(Model.vertices),
                "surface_count": len(Model.surfaces),
            },
        ),
    )
