from __future__ import annotations

import math
import struct

from convert.adapters.catia.Container import BuildCfvTwo, BuildDecl
from interchange import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepModel,
    BrepVertex,
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
    SpaceVector,
    SphereSurface,
    TorusSurface,
)

# this binding exists because shared behavior needs one stable value
KRefAngle = math.pi / 4.0

# this binding exists because shared behavior needs one stable value
KRefScale = 1.0e12

# this binding exists because shared behavior needs one stable value
KDelimiter = b"\x10\x24\x04\xff\xff\x00\x00\x00"

# this binding exists because shared behavior needs one stable value
KFbbRow = b"\x30\x04\x04\xff\xff\xe1\xe1\xe1"

# this binding exists because shared behavior needs one stable value
KPartStream = "1000_00000002_2"

# this binding exists because shared behavior needs one stable value
KProductStream = "1000_00000001_1"

# this binding exists because shared behavior needs one stable value
KGeomStream = "1000_00000003_3"

# this binding exists because shared behavior needs one stable value
KMfbrpStream = "1000_00000004_4"

# this binding exists because shared behavior needs one stable value
KSeeBodyStream = "1000_00000005_5"

# this binding exists because shared behavior needs one stable value
KBrepModeStream = "1000_00000006_6"

# this binding exists because shared behavior needs one stable value
KStdStream = "1000_00000007_7"

# this binding exists because shared behavior needs one stable value
KCgrStream = "1000_00000008_8"


# this definition exists because focused behavior needs one stable owner
def CanWrite(Model: BrepModel) -> bool:
    if not Model.faces or not Model.vertices or not Model.edges:
        return False
    if any(
        not isinstance(
            SurfaceValue,
            (
                PlaneSurface,
                CylinderSurface,
                ConeSurface,
                SphereSurface,
                TorusSurface,
            ),
        )
        for SurfaceValue in Model.surfaces
    ):
        return False
    return all(FaceValue.loop_ids for FaceValue in Model.faces)


# this definition exists because focused behavior needs one stable owner
def PackTrim(
    Loops: tuple[tuple[int, ...], ...],
    Width: int,
    VectorValue: tuple[float, float, float] | None,
) -> bytes:
    if not Loops or any(len(Loop) < 3 for Loop in Loops):
        raise ValueError("trim loop is too short")
    Handles = tuple(Handle for Loop in Loops for Handle in Loop)
    KindValue = 0x44 | (0x08 if VectorValue is not None else 0)
    DataValue = bytearray(b"\x01" + bytes([KindValue]))
    DataValue.append(len(Loops))
    DataValue.append(0xFF)
    DataValue.extend(struct.pack("<I", len(Handles)))
    if VectorValue is not None:
        DataValue.extend(struct.pack("<fff", *VectorValue))
    for Loop in Loops:
        DataValue.append(len(Loop))
    for Handle in Handles:
        DataValue.extend(Handle.to_bytes(Width, "big"))
    return bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def PackEdge(Edges: tuple[tuple[int, int], ...], Width: int) -> bytes:
    DataValue = bytearray(b"\x01\x02\xff")
    DataValue.extend(struct.pack("<I", len(Edges)))
    for Start, EndIndex in Edges:
        DataValue.extend(b"\x02\x02")
        DataValue.extend(Start.to_bytes(Width, "big"))
        DataValue.extend(EndIndex.to_bytes(Width, "big"))
    DataValue.extend(KDelimiter)
    return bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
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


# this definition exists because focused behavior needs one stable owner
def AxisPair(AxisValue: SpaceVector) -> tuple[float, float, float]:
    Values = (AxisValue.x, AxisValue.y, AxisValue.z)
    Length = math.sqrt(sum(Value * Value for Value in Values))
    if Length <= 1e-12:
        return (0.0, 0.0, 1.0)
    Values = (Values[0] / Length, Values[1] / Length, Values[2] / Length)
    if Values[2] < 0.0:
        return (-Values[0], -Values[1], -Values[2])
    return Values


# this definition exists because focused behavior needs one stable owner
def PackSurf(
    FaceValue: BrepFace, Points: tuple[SpaceVector, ...], Model: BrepModel
) -> bytes:
    SurfaceValue = next(
        Value for Value in Model.surfaces if Value.id == FaceValue.surface_id
    )
    XValues = [Point.x for Point in Points]
    YValues = [Point.y for Point in Points]
    ZValues = [Point.z for Point in Points]
    Center = (
        (min(XValues) + max(XValues)) / 2.0,
        (min(YValues) + max(YValues)) / 2.0,
        (min(ZValues) + max(ZValues)) / 2.0,
    )
    HalfExtent = (
        (max(XValues) - min(XValues)) / 2.0,
        (max(YValues) - min(YValues)) / 2.0,
        (max(ZValues) - min(ZValues)) / 2.0,
    )
    Radius = max(math.dist(Center, (Point.x, Point.y, Point.z)) for Point in Points)
    Bounds = (*Center, *HalfExtent, *Center, Radius)
    SignValue = 1 if getattr(FaceValue, "same_sense", True) else -1
    Tail = struct.pack("<10f", *Bounds) + struct.pack("b", SignValue) + b"\x00\x00\x00"
    if isinstance(SurfaceValue, CylinderSurface):
        AxisValue = AxisPair(SurfaceValue.axis)
        Carrier = (
            SurfaceValue.origin.x,
            SurfaceValue.origin.y,
            SurfaceValue.origin.z,
            AxisValue[0],
            AxisValue[1],
            SurfaceValue.radius,
        )
        return b"\x00\x02\x00\x33\x33" + struct.pack(">6f", *Carrier) + Tail
    if isinstance(SurfaceValue, ConeSurface):
        AxisValue = AxisPair(SurfaceValue.axis)
        Carrier = (
            SurfaceValue.origin.x,
            SurfaceValue.origin.y,
            SurfaceValue.origin.z,
            AxisValue[0],
            AxisValue[1],
            SurfaceValue.half_angle,
        )
        return b"\x00\x02\x00\x33\x34" + struct.pack(">6f", *Carrier) + Tail
    if isinstance(SurfaceValue, SphereSurface):
        SphereCarrier = (
            SurfaceValue.center.x,
            SurfaceValue.center.y,
            SurfaceValue.center.z,
            SurfaceValue.radius,
        )
        return b"\x00\x02\x00\x33\x35" + struct.pack(">4f", *SphereCarrier) + Tail
    if isinstance(SurfaceValue, TorusSurface):
        AxisValue = AxisPair(SurfaceValue.axis)
        TorusCarrier = (
            SurfaceValue.center.x,
            SurfaceValue.center.y,
            SurfaceValue.center.z,
            AxisValue[0],
            AxisValue[1],
            SurfaceValue.major_radius,
            SurfaceValue.minor_radius,
        )
        return b"\x00\x02\x00\x33\x38" + struct.pack(">7f", *TorusCarrier) + Tail
    return b"\x00\x02\x00\x33\x32" + Tail


# this definition exists because focused behavior needs one stable owner
def PackCurve(Index: int) -> bytes:
    return b"\x60" + Index.to_bytes(3, "little") + b"\x00\x02\x00\x33\x36\x00\x00"


# this definition exists because focused behavior needs one stable owner
def PackRoster(Count: int) -> bytes:
    return b"".join(
        b"\x54" + Index.to_bytes(3, "little") + b"\x00\x00\x00"
        for Index in range(Count)
    )


# this definition exists because focused behavior needs one stable owner
def FaceNormal(
    FaceValue: BrepFace, Model: BrepModel
) -> tuple[float, float, float] | None:
    SurfaceValue = next(
        Value for Value in Model.surfaces if Value.id == FaceValue.surface_id
    )
    if isinstance(SurfaceValue, PlaneSurface):
        Normal = SurfaceValue.normal
        return (Normal.x, Normal.y, Normal.z)
    return None


# this definition exists because focused behavior needs one stable owner
def FaceHandlesMut(
    FaceValue: BrepFace,
    Model: BrepModel,
    CoedgeById: dict[str, BrepCoedge],
    EdgeById: dict[str, BrepEdge],
    VertexIndex: dict[str, int],
    SeenPairs: set[tuple[int, int]],
    Edges: list[tuple[int, int]],
) -> tuple[tuple[int, ...], ...]:
    Loops: list[tuple[int, ...]] = []
    for LoopId in FaceValue.loop_ids:
        LoopValue = next(Value for Value in Model.loops if Value.id == LoopId)
        Handles: list[int] = []
        for CoedgeId in LoopValue.coedge_ids:
            CoedgeValue = CoedgeById[CoedgeId]
            EdgeValue = EdgeById[CoedgeValue.edge_id]
            Start = VertexIndex[EdgeValue.start_vertex_id]
            EndIndex = VertexIndex[EdgeValue.end_vertex_id]
            if CoedgeValue.reversed:
                Start, EndIndex = EndIndex, Start
            Handles.append(Start)
            HandlePair = (min(Start, EndIndex), max(Start, EndIndex))
            if HandlePair not in SeenPairs:
                SeenPairs.add(HandlePair)
                Edges.append(HandlePair)
        Loops.append(tuple(Handles))
    return tuple(Loops)


# this definition exists because focused behavior needs one stable owner
def BuildMain(Model: BrepModel) -> bytes:
    VertexIndex = {
        VertexValue.id: Index for Index, VertexValue in enumerate(Model.vertices)
    }
    CoedgeById = {Value.id: Value for Value in Model.coedges}
    EdgeById = {Value.id: Value for Value in Model.edges}
    Width = 2
    Trims: list[bytes] = []
    Edges: list[tuple[int, int]] = []
    SeenPairs: set[tuple[int, int]] = set()
    for FaceValue in Model.faces:
        Loops = FaceHandlesMut(
            FaceValue,
            Model,
            CoedgeById,
            EdgeById,
            VertexIndex,
            SeenPairs,
            Edges,
        )
        Trims.append(PackTrim(Loops, Width, FaceNormal(FaceValue, Model)))
    DataValue = bytearray(b"".join(Trims))
    DataValue.extend(KFbbRow * len(Model.faces))
    DataValue.extend(PackEdge(tuple(Edges), Width))
    DataValue.extend(PackVert(Model.vertices))
    return bytes(DataValue)


# this definition exists because focused behavior needs one stable owner
def BuildSurf(Model: BrepModel) -> bytes:
    VertexById = {VertexValue.id: VertexValue for VertexValue in Model.vertices}
    CoedgeById = {Value.id: Value for Value in Model.coedges}
    EdgeById = {Value.id: Value for Value in Model.edges}
    Records: list[bytes] = []
    for FaceValue in Model.faces:
        Points: list[SpaceVector] = []
        for LoopId in FaceValue.loop_ids:
            LoopValue = next(Value for Value in Model.loops if Value.id == LoopId)
            for CoedgeId in LoopValue.coedge_ids:
                CoedgeValue = CoedgeById[CoedgeId]
                EdgeValue = EdgeById[CoedgeValue.edge_id]
                VertexId = (
                    EdgeValue.end_vertex_id
                    if CoedgeValue.reversed
                    else EdgeValue.start_vertex_id
                )
                Points.append(VertexById[VertexId].point)
        Records.append(PackSurf(FaceValue, tuple(Points), Model))
    Records.extend(PackCurve(Index) for Index in range(len(Model.edges)))
    Records.extend((PackRoster(len(Model.vertices)),))
    Payload = b"".join(Records)
    Header = b"\xff" + len(Payload).to_bytes(3, "little") + b"\x00"
    Header += struct.pack("<ff", KRefAngle, KRefScale)
    Header += b"\x00" + struct.pack("<H", len(Payload) // 4) + b"\x00"
    return Header + Payload


# this definition exists because focused behavior needs one stable owner
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


# this definition exists because focused behavior needs one stable owner
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


# this definition exists because focused behavior needs one stable owner
def BuildDecls() -> bytes:
    return b"".join(
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


# this definition exists because focused behavior needs one stable owner
def BuildPart(Model: BrepModel) -> bytes:
    if not CanWrite(Model):
        raise ValueError("native CATIA writing supports plane faces with one loop")
    return BuildCfvTwo(
        (
            ("Format", b"CATPart"),
            ("Data", BuildDecls()),
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
