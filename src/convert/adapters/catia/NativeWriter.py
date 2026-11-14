from __future__ import annotations

import math
import struct

from convert.adapters.catia.Container import BuildCfvTwo, BuildDecl
from interchange import (
    BrepModel,
    BrepVertex,
    PlaneSurface,
    SpaceVector,
)

KRefAngle = math.pi / 4.0
KRefScale = 1.0e12
KDelimiter = b"\x10\x24\x04\xff\xff\x00\x00\x00"
KFbbRow = b"\x30\x04\x04\xff\xff\xe1\xe1\xe1"
KPartStream = "1000_00000002_2"
KProductStream = "1000_00000001_1"
KGeomStream = "1000_00000003_3"
KMfbrpStream = "1000_00000004_4"
KSeeBodyStream = "1000_00000005_5"
KBrepModeStream = "1000_00000006_6"
KStdStream = "1000_00000007_7"
KCgrStream = "1000_00000008_8"


def CanWrite(Model: BrepModel) -> bool:
    if not Model.faces or not Model.vertices or not Model.edges:
        return False
    if any(
        not isinstance(SurfaceValue, PlaneSurface) for SurfaceValue in Model.surfaces
    ):
        return False
    return all(len(FaceValue.loop_ids) == 1 for FaceValue in Model.faces)


def PackTrim(Handles: tuple[int, ...], Width: int) -> bytes:
    if len(Handles) < 3:
        raise ValueError("trim loop is too short")
    DataValue = bytearray(b"\x01\x44")
    DataValue.append(1)
    DataValue.append(0xFF)
    DataValue.extend(struct.pack("<I", len(Handles)))
    DataValue.append(len(Handles))
    for Handle in Handles:
        DataValue.extend(Handle.to_bytes(Width, "big"))
    return bytes(DataValue)


def PackEdge(Edges: tuple[tuple[int, int], ...], Width: int) -> bytes:
    DataValue = bytearray(b"\x01\x02\xff")
    DataValue.extend(struct.pack("<I", len(Edges)))
    for Start, End in Edges:
        DataValue.extend(b"\x02\x02")
        DataValue.extend(Start.to_bytes(Width, "big"))
        DataValue.extend(End.to_bytes(Width, "big"))
    DataValue.extend(KDelimiter)
    return bytes(DataValue)


def PackVert(Points: tuple[BrepVertex, ...]) -> bytes:
    DataValue = bytearray(b"\x01\x06\xff")
    DataValue.extend(struct.pack("<I", len(Points)))
    for Point in Points:
        DataValue.extend(b"\x05\x08\x01")
        DataValue.extend(
            struct.pack("<fff", Point.point.x, Point.point.y, Point.point.z)
        )
    DataValue.extend(KDelimiter)
    return bytes(DataValue)


def PackSurf(FaceValue: object, Points: tuple[SpaceVector, ...]) -> bytes:
    XValues = [Point.x for Point in Points]
    YValues = [Point.y for Point in Points]
    ZValues = [Point.z for Point in Points]
    Center = (
        (min(XValues) + max(XValues)) / 2.0,
        (min(YValues) + max(YValues)) / 2.0,
        (min(ZValues) + max(ZValues)) / 2.0,
    )
    Half = (
        (max(XValues) - min(XValues)) / 2.0,
        (max(YValues) - min(YValues)) / 2.0,
        (max(ZValues) - min(ZValues)) / 2.0,
    )
    Radius = max(math.dist(Center, (Point.x, Point.y, Point.z)) for Point in Points)
    Bounds = (*Center, *Half, *Center, Radius)
    Sign = 1 if getattr(FaceValue, "same_sense", True) else -1
    return (
        b"\x00\x02\x00\x33\x32"
        + struct.pack("<10f", *Bounds)
        + struct.pack("b", Sign)
        + b"\x00\x00\x00"
    )


def PackCurve(Index: int) -> bytes:
    return b"\x60" + Index.to_bytes(3, "little") + b"\x00\x02\x00\x33\x36\x00\x00"


def PackRoster(Count: int) -> bytes:
    return b"".join(
        b"\x54" + Index.to_bytes(3, "little") + b"\x00\x00\x00"
        for Index in range(Count)
    )


def BuildMain(Model: BrepModel) -> bytes:
    VertexIndex = {
        VertexValue.id: Index for Index, VertexValue in enumerate(Model.vertices)
    }
    Width = 2
    Trims: list[bytes] = []
    Edges: list[tuple[int, int]] = []
    Seen: set[tuple[int, int]] = set()
    for FaceValue in Model.faces:
        LoopValue = next(
            Value for Value in Model.loops if Value.id == FaceValue.loop_ids[0]
        )
        Handles: list[int] = []
        for CoedgeId in LoopValue.coedge_ids:
            CoedgeValue = next(Value for Value in Model.coedges if Value.id == CoedgeId)
            EdgeValue = next(
                Value for Value in Model.edges if Value.id == CoedgeValue.edge_id
            )
            Start = VertexIndex[EdgeValue.start_vertex_id]
            End = VertexIndex[EdgeValue.end_vertex_id]
            if CoedgeValue.reversed:
                Start, End = End, Start
            Handles.append(Start)
            Pair = (min(Start, End), max(Start, End))
            if Pair not in Seen:
                Seen.add(Pair)
                Edges.append(Pair)
        Trims.append(PackTrim(tuple(Handles), Width))
    DataValue = bytearray(b"".join(Trims))
    DataValue.extend(KFbbRow * len(Model.faces))
    DataValue.extend(PackEdge(tuple(Edges), Width))
    DataValue.extend(PackVert(Model.vertices))
    return bytes(DataValue)


def BuildSurf(Model: BrepModel) -> bytes:
    VertexById = {VertexValue.id: VertexValue for VertexValue in Model.vertices}
    Records: list[bytes] = []
    for FaceValue in Model.faces:
        LoopValue = next(
            Value for Value in Model.loops if Value.id == FaceValue.loop_ids[0]
        )
        Points: list[SpaceVector] = []
        for CoedgeId in LoopValue.coedge_ids:
            CoedgeValue = next(Value for Value in Model.coedges if Value.id == CoedgeId)
            EdgeValue = next(
                Value for Value in Model.edges if Value.id == CoedgeValue.edge_id
            )
            Points.append(VertexById[EdgeValue.start_vertex_id].point)
        Records.append(PackSurf(FaceValue, tuple(Points)))
    Records.extend(PackCurve(Index) for Index in range(len(Model.edges)))
    Records.extend((PackRoster(len(Model.vertices)),))
    Payload = b"".join(Records)
    Header = b"\xff" + len(Payload).to_bytes(3, "little") + b"\x00"
    Header += struct.pack("<ff", KRefAngle, KRefScale)
    Header += b"\x00" + struct.pack("<H", len(Payload) // 4) + b"\x00"
    return Header + Payload


def BuildNest(Model: BrepModel) -> bytes:
    return BuildCfvTwo(
        (
            ("00000000000000000000", b"\x00" * 132),
            ("MAIN", b"\x00" * 9),
            ("Describe", b"\x00" * 88),
            ("MainDataStream", BuildMain(Model)),
            ("Header", b"\x00" * 84),
            ("SceneGraph", b"\x00" * 132),
            ("SurfacicReps", BuildSurf(Model)),
        )
    )


def Summary() -> bytes:
    NameValue = b"CATSummaryInformation"
    Version = b"FirstStreamed<Version>5/<Version><Release>28/<Release><ServicePack>6/<ServicePack><BuildDate>03-10-2020.20.00/<BuildDate><HotFix>0/<HotFix>LastSaveVersion<Version>5/<Version><Release>28/<Release><ServicePack>6/<ServicePack><BuildDate>03-10-2020.20.00/<BuildDate><HotFix>0/<HotFix>MinimalVersionToReadCATIAV5R28"
    return b"".join(
        (
            b"FINJPL  ",
            struct.pack(">I", 16842755),
            struct.pack(">I", len(NameValue)),
            b"\x00",
            NameValue,
            b"DASSAULT-SYSTEMES",
            b"CATPart",
            Version,
        )
    )


def BuildPart(Model: BrepModel) -> bytes:
    if not CanWrite(Model):
        raise ValueError("native CATIA writing supports plane faces with one loop")
    Declarations = b"".join(
        (
            BuildDecl("CATProdCont", "CATFeatCont", KProductStream, 1),
            BuildDecl("CATPrtCont", "CATProdCont", KPartStream, 2),
            BuildDecl("CGMGeom", "CATFeatCont", KGeomStream, 3),
            BuildDecl("CATMFBRP", "CATFeatCont", KMfbrpStream, 4),
            BuildDecl("CATSeeBodyCont", "CATFeatCont", KSeeBodyStream, 5),
            BuildDecl("CATBRepModeContainer", "CATFeatCont", KBrepModeStream, 6),
            BuildDecl("CATStdCont", "CATFeatCont", KStdStream, 7),
            BuildDecl("CATCGRCont", "CATFeatCont", KCgrStream, 8),
        )
    )
    return BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", Declarations),
            (KProductStream, b"\x00"),
            (KPartStream, b"\x00"),
            (KGeomStream, BuildNest(Model)),
            (KMfbrpStream, b"\x00"),
            (KSeeBodyStream, b"\x00"),
            (KBrepModeStream, b"\x00"),
            (KStdStream, b"\x00"),
            (KCgrStream, b"\x00"),
            ("CATSummaryInformation", Summary()),
        )
    )
