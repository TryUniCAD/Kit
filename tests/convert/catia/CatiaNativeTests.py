from __future__ import annotations

import math
from pathlib import Path

from convert import open_document as OpenDoc
from convert.adapters import WriteOptions
from convert.adapters.catia.Adapter import CatiaAdapter, ReadCatia
from convert.adapters.catia.Container import CfvTwoArchive
from convert.adapters.catia.NativeBrep import (
    BuildVertices,
    DecodeBrep,
    DecodeTess,
    LocalFrame,
    ParseBrep,
)
from interchange import (
    Body,
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
    CadDocument,
    CadSource,
    CircleCurve,
    ConeSurface,
    CylinderSurface,
    LineCurve,
    PlaneSurface,
    SpaceVector,
)

# this binding exists because shared behavior needs one stable value
KRootValue = Path(__file__).parents[3]

# this binding exists because shared behavior needs one stable value
KCatparts = KRootValue / "re" / "catia" / "examples" / ".CATPart"

# this binding exists because shared behavior needs one stable value
KQuads = (
    (0, 3, 2, 1),
    (4, 5, 6, 7),
    (0, 1, 5, 4),
    (1, 2, 6, 5),
    (2, 3, 7, 6),
    (3, 0, 4, 7),
)


# this definition exists because focused behavior needs one stable owner
def BoxPoints() -> list[SpaceVector]:
    return [
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(1.0, 1.0, 0.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 1.0),
        SpaceVector(1.0, 1.0, 1.0),
        SpaceVector(0.0, 1.0, 1.0),
    ]


# this definition exists because focused behavior needs one stable owner
def BoxFaces(
    Points: list[SpaceVector],
) -> tuple[
    list[LineCurve],
    list[BrepEdge],
    list[BrepCoedge],
    list[BrepLoop],
    list[BrepFace],
]:
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []
    Loops: list[BrepLoop] = []
    Faces: list[BrepFace] = []
    for FaceIndex, QuadValue in enumerate(KQuads):
        CoedgeIds: list[str] = []
        for Position in range(4):
            Start = QuadValue[Position]
            EndIndex = QuadValue[(Position + 1) % 4]
            CurveId = f"catia:curve:{len(Curves) + 1}"
            Direction = SpaceVector(
                Points[EndIndex].x - Points[Start].x,
                Points[EndIndex].y - Points[Start].y,
                Points[EndIndex].z - Points[Start].z,
            )
            Curves.append(LineCurve(CurveId, Points[Start], Direction))
            EdgeId = f"catia:edge:{len(Edges) + 1}"
            Edges.append(
                BrepEdge(
                    EdgeId,
                    f"catia:vertex:{Start + 1}",
                    f"catia:vertex:{EndIndex + 1}",
                    CurveId,
                    0.0,
                    1.0,
                )
            )
            CoedgeId = f"catia:coedge:{len(Coedges) + 1}"
            Coedges.append(BrepCoedge(CoedgeId, EdgeId))
            CoedgeIds.append(CoedgeId)
        LoopId = f"catia:loop:{FaceIndex + 1}"
        Loops.append(BrepLoop(LoopId, tuple(CoedgeIds), outer=True))
        Faces.append(
            BrepFace(
                f"catia:face:{FaceIndex + 1}",
                f"catia:surface:{FaceIndex + 1}",
                (LoopId,),
            )
        )
    return Curves, Edges, Coedges, Loops, Faces


# this definition exists because focused behavior needs one stable owner
def BoxModel() -> BrepModel:
    Points = BoxPoints()
    Vertices = tuple(
        BrepVertex(f"catia:vertex:{Index + 1}", Point)
        for Index, Point in enumerate(Points)
    )
    Curves, Edges, Coedges, Loops, Faces = BoxFaces(Points)
    Surfaces = tuple(
        PlaneSurface(
            f"catia:surface:{Index + 1}",
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.0, 0.0, 1.0),
            SpaceVector(1.0, 0.0, 0.0),
        )
        for Index in range(6)
    )
    FaceUses = tuple(
        BrepFaceUse(f"catia:face-use:{Index + 1}", FaceValue.id)
        for Index, FaceValue in enumerate(Faces)
    )
    Shell = BrepShell(
        "catia:shell:1", tuple(Value.id for Value in FaceUses), closed=True
    )
    ShellUse = BrepShellUse("catia:shell-use:1", Shell.id)
    Region = BrepRegion("catia:region:1", (ShellUse.id,), solid=True)
    BodyValue = BrepBody("catia:body:1", (Region.id,), design_body_id="catia:body:1")
    return BrepModel(
        curves=tuple(Curves),
        surfaces=Surfaces,
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
def TestBrepCorpus() -> None:
    Decoded = 0
    for PathValue in sorted(KCatparts.glob("*.CATPart")):
        DocValue = OpenDoc(PathValue)
        if DocValue.brep is None:
            continue
        Decoded += 1
        assert DocValue.brep.validate(frozenset({"catia:body:1"})) == ()
        assert DocValue.brep.faces
        assert DocValue.brep.edges
        assert DocValue.brep.vertices
    assert Decoded >= 27


# this definition exists because focused behavior needs one stable owner
def TestBrepHeur() -> None:
    Archive = CfvTwoArchive.from_bytes((KCatparts / "Reservoir.CATPart").read_bytes())
    Model, Diagnostics = DecodeBrep(Archive)
    assert Model is not None
    assert any(
        Value.code == "catia.brep.native_surface_map_heuristic" for Value in Diagnostics
    )
    assert len(Model.faces) == 71
    assert len(Model.surfaces) == 71


# this definition exists because focused behavior needs one stable owner
def TestBrepTess() -> None:
    Archive = CfvTwoArchive.from_bytes(
        (KCatparts / "Copper_Washer.CATPart").read_bytes()
    )
    Points = DecodeTess(Archive)
    assert len(Points) >= 40
    Outer = {
        round(8.0 * math.cos(math.radians(18.0 * StepValue)), 3)
        for StepValue in range(20)
    } | {
        round(8.0 * math.sin(math.radians(18.0 * StepValue)), 3)
        for StepValue in range(20)
    }
    Inner = {
        round(5.0 * math.cos(math.radians(22.5 * StepValue)), 3)
        for StepValue in range(16)
    } | {
        round(5.0 * math.sin(math.radians(22.5 * StepValue)), 3)
        for StepValue in range(16)
    }
    for YValue, ZValue in Points:
        Radius = math.hypot(YValue, ZValue)
        assert abs(Radius - 8.0) < 1e-2 or abs(Radius - 5.0) < 1e-2
        Table = Outer if abs(Radius - 8.0) < 1e-2 else Inner
        assert round(abs(YValue), 3) in Table
        assert round(abs(ZValue), 3) in Table
    BrepValue = ParseBrep(Archive)
    Vertices, _ = BuildVertices(BrepValue)
    Frame = LocalFrame(BrepValue)
    assert Frame is not None
    First, Second, _ = Frame
    OnGrid = 0
    for VertexValue in Vertices:
        Point = VertexValue.point
        FirstValue = Point.x * First[0] + Point.y * First[1] + Point.z * First[2]
        SecondValue = Point.x * Second[0] + Point.y * Second[1] + Point.z * Second[2]
        Radius = math.hypot(FirstValue, SecondValue)
        Table = Outer if abs(Radius - 8.0) < 1e-2 else Inner
        if round(abs(FirstValue), 3) in Table and round(abs(SecondValue), 3) in Table:
            OnGrid += 1
    assert OnGrid == len(Vertices)


# this definition exists because focused behavior needs one stable owner
def TestBrepWriter(TmpPath: Path) -> None:
    Model = BoxModel()
    DocValue = CadDocument(
        source=CadSource("catia.v5", "box.CATPart", "0" * 64),
        configurations=(),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(Body("catia:body:1", "Box", ""),),
        brep=Model,
    )
    Output = TmpPath / "box.CATPart"
    Result = CatiaAdapter().write(
        DocValue,
        Output,
        WriteOptions(validate=False, values={"native_brep": True}),
    )
    assert Result.metadata["mode"] == "native_brep"
    assert Result.metadata["native_geometry"] is True
    assert Result.metadata["vendor_loadable"] is False
    Restored = ReadCatia(Output)
    assert Restored.brep is not None
    assert len(Restored.brep.faces) == 6
    assert len(Restored.brep.edges) == 12
    assert len(Restored.brep.vertices) == 8
    assert Restored.brep.validate(frozenset({"catia:body:1"})) == ()


# this definition exists because focused behavior needs one stable owner
def CylinderModel() -> BrepModel:
    Radius = 2.5
    Height = 1.0
    Points = [
        SpaceVector(
            Radius * math.cos(math.pi / 2.0 * StepValue),
            Radius * math.sin(math.pi / 2.0 * StepValue),
            Level,
        )
        for Level in (0.0, Height)
        for StepValue in range(4)
    ]
    Vertices = tuple(
        BrepVertex(f"catia:vertex:{Index + 1}", Point)
        for Index, Point in enumerate(Points)
    )
    Curves: list[CircleCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []

    def AddEdge(Start: int, EndIndex: int, Center: SpaceVector) -> str:
        CurveId = f"catia:curve:{len(Curves) + 1}"
        Curves.append(
            CircleCurve(
                CurveId,
                Center,
                SpaceVector(0.0, 0.0, 1.0),
                SpaceVector(1.0, 0.0, 0.0),
                Radius,
            )
        )
        EdgeId = f"catia:edge:{len(Edges) + 1}"
        Edges.append(
            BrepEdge(
                EdgeId,
                f"catia:vertex:{Start + 1}",
                f"catia:vertex:{EndIndex + 1}",
                CurveId,
                0.0,
                1.0,
            )
        )
        CoedgeId = f"catia:coedge:{len(Coedges) + 1}"
        Coedges.append(BrepCoedge(CoedgeId, EdgeId))
        return CoedgeId

    Bottom = [
        AddEdge(StepValue, (StepValue + 1) % 4, SpaceVector(0.0, 0.0, 0.0))
        for StepValue in range(4)
    ]
    TopValue = [
        AddEdge(4 + StepValue, 4 + (StepValue + 1) % 4, SpaceVector(0.0, 0.0, Height))
        for StepValue in range(4)
    ]
    UpValue = AddEdge(0, 4, SpaceVector(0.0, 0.0, 0.0))
    DownValue = AddEdge(4, 0, SpaceVector(0.0, 0.0, 0.0))
    Loops = (
        BrepLoop("catia:loop:1", tuple(Bottom), outer=True),
        BrepLoop("catia:loop:2", tuple(TopValue), outer=True),
        BrepLoop(
            "catia:loop:3",
            tuple(Bottom) + (UpValue,) + tuple(TopValue) + (DownValue,),
            outer=True,
        ),
    )
    Faces = (
        BrepFace("catia:face:1", "catia:surface:1", ("catia:loop:1",)),
        BrepFace("catia:face:2", "catia:surface:2", ("catia:loop:2",)),
        BrepFace("catia:face:3", "catia:surface:3", ("catia:loop:3",)),
    )
    Surfaces = (
        PlaneSurface(
            "catia:surface:1",
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.0, 0.0, -1.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
        PlaneSurface(
            "catia:surface:2",
            SpaceVector(0.0, 0.0, Height),
            SpaceVector(0.0, 0.0, 1.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
        CylinderSurface(
            "catia:surface:3",
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.0, 0.0, 1.0),
            SpaceVector(1.0, 0.0, 0.0),
            Radius,
        ),
    )
    FaceUses = tuple(
        BrepFaceUse(f"catia:face-use:{Index + 1}", FaceValue.id)
        for Index, FaceValue in enumerate(Faces)
    )
    Shell = BrepShell(
        "catia:shell:1", tuple(Value.id for Value in FaceUses), closed=True
    )
    ShellUse = BrepShellUse("catia:shell-use:1", Shell.id)
    Region = BrepRegion("catia:region:1", (ShellUse.id,), solid=True)
    BodyValue = BrepBody("catia:body:1", (Region.id,), design_body_id="catia:body:1")
    return BrepModel(
        curves=tuple(Curves),
        surfaces=Surfaces,
        vertices=Vertices,
        edges=tuple(Edges),
        coedges=tuple(Coedges),
        loops=Loops,
        faces=Faces,
        face_uses=FaceUses,
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(BodyValue,),
    )


# this definition exists because focused behavior needs one stable owner
def TestBrepCyl(TmpPath: Path) -> None:
    Model = CylinderModel()
    assert Model.validate(frozenset({"catia:body:1"})) == ()
    DocValue = CadDocument(
        source=CadSource("catia.v5", "cylinder.CATPart", "0" * 64),
        configurations=(),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(Body("catia:body:1", "Cylinder", ""),),
        brep=Model,
    )
    Output = TmpPath / "cylinder.CATPart"
    Result = CatiaAdapter().write(
        DocValue,
        Output,
        WriteOptions(validate=False, values={"native_brep": True}),
    )
    assert Result.metadata["mode"] == "native_brep"
    assert Result.metadata["native_geometry"] is True
    assert Result.metadata["vendor_loadable"] is False
    Restored = ReadCatia(Output)
    assert Restored.brep is not None
    assert len(Restored.brep.faces) == 3
    assert len(Restored.brep.vertices) == 8
    Kinds = [type(Value).__name__ for Value in Restored.brep.surfaces]
    assert Kinds.count("CylinderSurface") == 1
    assert Kinds.count("PlaneSurface") == 2
    CylinderValue = next(
        Value for Value in Restored.brep.surfaces if isinstance(Value, CylinderSurface)
    )
    assert abs(CylinderValue.radius - 2.5) < 1e-4
    assert abs(CylinderValue.axis.z - 1.0) < 1e-4
    assert Restored.brep.validate(frozenset({"catia:body:1"})) == ()


# this definition exists because focused behavior needs one stable owner
def ConeModel() -> BrepModel:
    BottomRadius = 2.0
    TopRadius = 1.0
    Height = 1.0
    Points = [
        SpaceVector(
            BottomRadius * math.cos(math.pi / 2.0 * StepValue),
            BottomRadius * math.sin(math.pi / 2.0 * StepValue),
            0.0,
        )
        for StepValue in range(4)
    ] + [
        SpaceVector(
            TopRadius * math.cos(math.pi / 2.0 * StepValue),
            TopRadius * math.sin(math.pi / 2.0 * StepValue),
            Height,
        )
        for StepValue in range(4)
    ]
    Vertices = tuple(
        BrepVertex(f"catia:vertex:{Index + 1}", Point)
        for Index, Point in enumerate(Points)
    )
    Curves: list[CircleCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []

    def AddEdge(Start: int, EndIndex: int, Center: SpaceVector, Radius: float) -> str:
        CurveId = f"catia:curve:{len(Curves) + 1}"
        Curves.append(
            CircleCurve(
                CurveId,
                Center,
                SpaceVector(0.0, 0.0, 1.0),
                SpaceVector(1.0, 0.0, 0.0),
                Radius,
            )
        )
        EdgeId = f"catia:edge:{len(Edges) + 1}"
        Edges.append(
            BrepEdge(
                EdgeId,
                f"catia:vertex:{Start + 1}",
                f"catia:vertex:{EndIndex + 1}",
                CurveId,
                0.0,
                1.0,
            )
        )
        CoedgeId = f"catia:coedge:{len(Coedges) + 1}"
        Coedges.append(BrepCoedge(CoedgeId, EdgeId))
        return CoedgeId

    Bottom = [
        AddEdge(
            StepValue, (StepValue + 1) % 4, SpaceVector(0.0, 0.0, 0.0), BottomRadius
        )
        for StepValue in range(4)
    ]
    TopValue = [
        AddEdge(
            4 + StepValue,
            4 + (StepValue + 1) % 4,
            SpaceVector(0.0, 0.0, Height),
            TopRadius,
        )
        for StepValue in range(4)
    ]
    UpValue = AddEdge(0, 4, SpaceVector(0.0, 0.0, 0.0), BottomRadius)
    DownValue = AddEdge(4, 0, SpaceVector(0.0, 0.0, 0.0), BottomRadius)
    Loops = (
        BrepLoop("catia:loop:1", tuple(Bottom), outer=True),
        BrepLoop("catia:loop:2", tuple(TopValue), outer=True),
        BrepLoop(
            "catia:loop:3",
            tuple(Bottom) + (UpValue,) + tuple(TopValue) + (DownValue,),
            outer=True,
        ),
    )
    Faces = (
        BrepFace("catia:face:1", "catia:surface:1", ("catia:loop:1",)),
        BrepFace("catia:face:2", "catia:surface:2", ("catia:loop:2",)),
        BrepFace("catia:face:3", "catia:surface:3", ("catia:loop:3",)),
    )
    Surfaces = (
        PlaneSurface(
            "catia:surface:1",
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.0, 0.0, -1.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
        PlaneSurface(
            "catia:surface:2",
            SpaceVector(0.0, 0.0, Height),
            SpaceVector(0.0, 0.0, 1.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
        ConeSurface(
            "catia:surface:3",
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.0, 0.0, 1.0),
            SpaceVector(1.0, 0.0, 0.0),
            BottomRadius,
            math.atan((BottomRadius - TopRadius) / Height),
        ),
    )
    FaceUses = tuple(
        BrepFaceUse(f"catia:face-use:{Index + 1}", FaceValue.id)
        for Index, FaceValue in enumerate(Faces)
    )
    Shell = BrepShell(
        "catia:shell:1", tuple(Value.id for Value in FaceUses), closed=True
    )
    ShellUse = BrepShellUse("catia:shell-use:1", Shell.id)
    Region = BrepRegion("catia:region:1", (ShellUse.id,), solid=True)
    BodyValue = BrepBody("catia:body:1", (Region.id,), design_body_id="catia:body:1")
    return BrepModel(
        curves=tuple(Curves),
        surfaces=Surfaces,
        vertices=Vertices,
        edges=tuple(Edges),
        coedges=tuple(Coedges),
        loops=Loops,
        faces=Faces,
        face_uses=FaceUses,
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(BodyValue,),
    )


# this definition exists because focused behavior needs one stable owner
def TestBrepCone(TmpPath: Path) -> None:
    Model = ConeModel()
    assert Model.validate(frozenset({"catia:body:1"})) == ()
    DocValue = CadDocument(
        source=CadSource("catia.v5", "cone.CATPart", "0" * 64),
        configurations=(),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(Body("catia:body:1", "Cone", ""),),
        brep=Model,
    )
    Output = TmpPath / "cone.CATPart"
    Result = CatiaAdapter().write(
        DocValue,
        Output,
        WriteOptions(validate=False, values={"native_brep": True}),
    )
    assert Result.metadata["mode"] == "native_brep"
    Restored = ReadCatia(Output)
    assert Restored.brep is not None
    assert len(Restored.brep.faces) == 3
    Kinds = [type(Value).__name__ for Value in Restored.brep.surfaces]
    assert Kinds.count("ConeSurface") == 1
    assert Kinds.count("PlaneSurface") == 2
    ConeValue = next(
        Value for Value in Restored.brep.surfaces if isinstance(Value, ConeSurface)
    )
    assert abs(ConeValue.half_angle - math.atan(1.0)) < 1e-4
    assert Restored.brep.validate(frozenset({"catia:body:1"})) == ()


# this definition exists because focused behavior needs one stable owner
def TwoLoopModel() -> BrepModel:
    Points = [
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(2.0, 0.0, 0.0),
        SpaceVector(3.0, 0.0, 0.0),
        SpaceVector(2.0, 1.0, 0.0),
    ]
    Vertices = tuple(
        BrepVertex(f"catia:vertex:{Index + 1}", Point)
        for Index, Point in enumerate(Points)
    )
    Curves: list[LineCurve] = []
    Edges: list[BrepEdge] = []
    Coedges: list[BrepCoedge] = []

    def AddEdge(Start: int, EndIndex: int) -> str:
        CurveId = f"catia:curve:{len(Curves) + 1}"
        Curves.append(
            LineCurve(
                CurveId,
                Points[Start],
                SpaceVector(
                    Points[EndIndex].x - Points[Start].x,
                    Points[EndIndex].y - Points[Start].y,
                    Points[EndIndex].z - Points[Start].z,
                ),
            )
        )
        EdgeId = f"catia:edge:{len(Edges) + 1}"
        Edges.append(
            BrepEdge(
                EdgeId,
                f"catia:vertex:{Start + 1}",
                f"catia:vertex:{EndIndex + 1}",
                CurveId,
                0.0,
                1.0,
            )
        )
        CoedgeId = f"catia:coedge:{len(Coedges) + 1}"
        Coedges.append(BrepCoedge(CoedgeId, EdgeId))
        return CoedgeId

    Outer = [AddEdge(0, 1), AddEdge(1, 2), AddEdge(2, 0)]
    Inner = [AddEdge(3, 4), AddEdge(4, 5), AddEdge(5, 3)]
    Loops = (
        BrepLoop("catia:loop:1", tuple(Outer), outer=True),
        BrepLoop("catia:loop:2", tuple(Inner), outer=False),
    )
    Faces = (
        BrepFace("catia:face:1", "catia:surface:1", ("catia:loop:1", "catia:loop:2")),
    )
    Surfaces = (
        PlaneSurface(
            "catia:surface:1",
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(0.0, 0.0, 1.0),
            SpaceVector(1.0, 0.0, 0.0),
        ),
    )
    FaceUses = (BrepFaceUse("catia:face-use:1", Faces[0].id),)
    Shell = BrepShell("catia:shell:1", (FaceUses[0].id,), closed=True)
    ShellUse = BrepShellUse("catia:shell-use:1", Shell.id)
    Region = BrepRegion("catia:region:1", (ShellUse.id,), solid=True)
    BodyValue = BrepBody("catia:body:1", (Region.id,), design_body_id="catia:body:1")
    return BrepModel(
        curves=tuple(Curves),
        surfaces=Surfaces,
        vertices=Vertices,
        edges=tuple(Edges),
        coedges=tuple(Coedges),
        loops=Loops,
        faces=Faces,
        face_uses=FaceUses,
        shells=(Shell,),
        shell_uses=(ShellUse,),
        regions=(Region,),
        bodies=(BodyValue,),
    )


def TestBrepTwoLoop(TmpPath: Path) -> None:
    Model = TwoLoopModel()
    assert Model.validate(frozenset({"catia:body:1"})) == ()
    DocValue = CadDocument(
        source=CadSource("catia.v5", "two.CATPart", "0" * 64),
        configurations=(),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(Body("catia:body:1", "Two", ""),),
        brep=Model,
    )
    Output = TmpPath / "two.CATPart"
    Result = CatiaAdapter().write(
        DocValue,
        Output,
        WriteOptions(validate=False, values={"native_brep": True}),
    )
    assert Result.metadata["mode"] == "native_brep"
    Restored = ReadCatia(Output)
    assert Restored.brep is not None
    assert len(Restored.brep.faces) == 1
    assert len(Restored.brep.faces[0].loop_ids) == 2
    assert len(Restored.brep.loops) == 2
    assert Restored.brep.validate(frozenset({"catia:body:1"})) == ()
