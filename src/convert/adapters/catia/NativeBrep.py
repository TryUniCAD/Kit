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
    BrepVertex,
    Diagnostic,
    LineCurve,
    Severity,
    SpaceVector,
)

KBodyId = "catia:body:1"


@dataclass(frozen=True, slots=True)
class BrepData:
    surfaces: tuple[SurfaceRec, ...]
    trims: tuple[TrimRec, ...]
    edges: tuple[EdgeRec, ...]
    vertices: tuple[VertRec, ...]
    roster: tuple[VertRec, ...]
    width: int


def Vector(Values: tuple[float, float, float]) -> SpaceVector:
    return SpaceVector(*Values)


def Normalize(Values: tuple[float, float, float]) -> tuple[float, float, float]:
    Length = math.sqrt(sum(Value * Value for Value in Values))
    if Length <= 1e-12:
        return (1.0, 0.0, 0.0)
    return (
        Values[0] / Length,
        Values[1] / Length,
        Values[2] / Length,
    )


def Largest(Folder: CfvTwoFolder, NameValue: str) -> CfvTwoStream:
    Matches = tuple(Stream for Stream in Folder.streams if Stream.name == NameValue)
    if not Matches:
        raise ValueError(f"{NameValue} stream is missing")
    return max(Matches, key=lambda Stream: Stream.logical_length)


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


def BuildBrep(Data: BrepData) -> BrepModel:
    if not Data.vertices:
        raise ValueError("vertex table is empty")
    Handles = sorted(
        {Handle for TrimValue in Data.trims for Handle in TrimValue.handles}
    )
    VertexByHandle: dict[int, str] = {}
    Vertices: list[BrepVertex] = [
        BrepVertex(f"catia:vertex:{Index + 1}", Vector(Row.point))
        for Index, Row in enumerate(Data.vertices)
    ]
    for Handle in Handles:
        VertexByHandle[Handle] = f"catia:vertex:{(Handle % len(Data.vertices)) + 1}"
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    EdgeByPair: dict[tuple[int, int], str] = {}
    Coedges: list[BrepCoedge] = []
    Loops: list[BrepLoop] = []
    Faces: list[BrepFace] = []
    Surfaces: list[object] = []
    for FaceIndex, (SurfaceValue, TrimValue) in enumerate(
        zip(Data.surfaces, Data.trims), start=1
    ):
        Surfaces.append(MakeSurf(SurfaceValue, FaceIndex, TrimValue.vector))
        LoopIds: list[str] = []
        for CycleIndex, Cycle in enumerate(Boundary(TrimValue), start=1):
            CoedgeIds: list[str] = []
            for Position, StartHandle in enumerate(Cycle):
                EndHandle = Cycle[(Position + 1) % len(Cycle)]
                Pair = (min(StartHandle, EndHandle), max(StartHandle, EndHandle))
                EdgeId = EdgeByPair.get(Pair)
                if EdgeId is None:
                    EdgeId = f"catia:edge:{len(Edges) + 1}"
                    EdgeByPair[Pair] = EdgeId
                    StartId = VertexByHandle[Pair[0]]
                    EndId = VertexByHandle[Pair[1]]
                    StartPoint = next(
                        Value.point for Value in Vertices if Value.id == StartId
                    )
                    EndPoint = next(
                        Value.point for Value in Vertices if Value.id == EndId
                    )
                    Direction = Normalize(
                        (
                            EndPoint.x - StartPoint.x,
                            EndPoint.y - StartPoint.y,
                            EndPoint.z - StartPoint.z,
                        )
                    )
                    CurveId = f"catia:curve:{len(Curves) + 1}"
                    Curves.append(LineCurve(CurveId, StartPoint, Vector(Direction)))
                    Length = math.dist(
                        (StartPoint.x, StartPoint.y, StartPoint.z),
                        (EndPoint.x, EndPoint.y, EndPoint.z),
                    )
                    Edges.append(BrepEdge(EdgeId, StartId, EndId, CurveId, 0.0, Length))
                CoedgeId = f"catia:coedge:{len(Coedges) + 1}"
                Coedges.append(
                    BrepCoedge(CoedgeId, EdgeId, reversed=StartHandle > EndHandle)
                )
                CoedgeIds.append(CoedgeId)
            LoopId = f"catia:loop:{FaceIndex}:{CycleIndex}"
            Loops.append(BrepLoop(LoopId, tuple(CoedgeIds), outer=CycleIndex == 1))
            LoopIds.append(LoopId)
        Faces.append(
            BrepFace(
                f"catia:face:{FaceIndex}",
                f"catia:surface:{FaceIndex}",
                tuple(LoopIds),
                same_sense=SurfaceValue.sign >= 0,
            )
        )
    FaceUses = tuple(
        BrepFaceUse(f"catia:face-use:{Index}", FaceValue.id)
        for Index, FaceValue in enumerate(Faces, start=1)
    )
    Shell = BrepShell(
        "catia:shell:1", tuple(Value.id for Value in FaceUses), closed=True
    )
    ShellUse = BrepShellUse("catia:shell-use:1", Shell.id)
    Region = BrepRegion("catia:region:1", (ShellUse.id,), solid=True)
    Body = BrepBody(KBodyId, (Region.id,), design_body_id=KBodyId)
    return BrepModel(
        curves=tuple(Curves),
        surfaces=tuple(Surfaces),
        vertices=tuple(Vertices),
        edges=tuple(Edges),
        coedges=tuple(Coedges),
        loops=tuple(Loops),
        faces=tuple(Faces),
        face_uses=FaceUses,
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(Body,),
    )


def DecodeBrep(
    Archive: CfvTwoArchive,
) -> tuple[BrepModel | None, tuple[Diagnostic, ...]]:
    try:
        Data = ParseBrep(Archive)
        Model = BuildBrep(Data)
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
