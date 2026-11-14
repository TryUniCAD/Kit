from __future__ import annotations

from pathlib import Path

from convert import open_document as OpenDoc
from convert.adapters import WriteOptions
from convert.adapters.catia.Adapter import CatiaAdapter, ReadCatia
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
    assert Decoded >= 25


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
