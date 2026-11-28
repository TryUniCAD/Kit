from collections import Counter as CountKinds
from dataclasses import replace as ReplaceValue
from json import loads as LoadJson
from math import isclose as IsClose
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from convert import open_document as OpenDocument
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import (
    LowerBoxModel,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import (
    MakeOriginBox,
)
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)

# the synchronized cohort contains an independently authored dimensional rectangle
KCorpus = KRepoRoot / "re/solidworks/v2026/corpus"

# the older mixed profile exercises actual circle and rectangle coexistence
KLegacyPart = (
    KRepoRoot
    / "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024"
    / "CULATA_IZQUIERDO.SLDPRT"
)


# a native dimensioned rectangle must retain its two linear drives and real extent
def TestRectOpen() -> None:
    Document = OpenDocument(
        KCorpus / "assembly-synchronized/A13SyncedSingleChild.SLDPRT",
        include_brep=False,
        include_tessellation=False,
    )
    assert not Document.validate()
    (Sketch,) = Document.sketches
    assert CountKinds(str(Entity.kind) for Entity in Sketch.entities) == {"line": 4}
    assert [len(LoopValue) for LoopValue in Sketch.closed_profile_entity_ids] == [4]
    assert {
        Relation.parameter_id: (
            Relation.kind,
            Relation.driving,
            tuple(
                (RefValue.entity_id, RefValue.point) for RefValue in Relation.references
            ),
        )
        for Relation in Sketch.constraints
        if Relation.parameter_id
    } == {
        "sldprt:parameter:26:D1": (
            "distance",
            True,
            ((f"{Sketch.id}:line:1", "start"), (f"{Sketch.id}:line:1", "end")),
        ),
        "sldprt:parameter:26:D2": (
            "distance",
            True,
            ((f"{Sketch.id}:line:2", "start"), (f"{Sketch.id}:line:2", "end")),
        ),
    }
    Bounds = Document.bodies[0].topology.bounding_box
    assert Bounds is not None
    assert Bounds.minimum == SpaceVector(-20.0, -10.0, 0.0)
    assert Bounds.maximum == SpaceVector(20.0, 10.0, 10.0)


# the native shell must bound positive volume when its directed loops are integrated
def TestRectWinding() -> None:
    Document = OpenDocument(
        KCorpus / "ladder/L1_boss.SLDPRT", include_tessellation=False
    )
    Model = Document.brep
    assert Model is not None
    assert not Document.validate()
    Vertices = {Vertex.id: Vertex.point for Vertex in Model.vertices}
    Edges = {EdgeData.id: EdgeData for EdgeData in Model.edges}
    Starts = {
        Coedge.id: Vertices[
            (
                Edges[Coedge.edge_id].end_vertex_id
                if Coedge.reversed
                else Edges[Coedge.edge_id].start_vertex_id
            )
        ]
        for Coedge in Model.coedges
    }
    assert len(Model.loops) == 6
    Volume = 0.0
    for LoopValue in Model.loops:
        First, Second, Third, Fourth = tuple(
            Starts[UseId] for UseId in LoopValue.coedge_ids
        )
        Volume += DotVector(First, CrossVector(Second, Third))
        Volume += DotVector(First, CrossVector(Third, Fourth))
    assert IsClose(Volume / 6.0, 8000.0, abs_tol=1e-9)


# current sketches with an actual arc array must keep their circular geometry
def TestAnnulus() -> None:
    Document = OpenDocument(
        KCorpus / "curves-discovery/D19Annulus.SLDPRT",
        include_brep=False,
        include_tessellation=False,
    )
    assert not Document.validate()
    (Sketch,) = Document.sketches
    assert CountKinds(str(Entity.kind) for Entity in Sketch.entities) == {
        "circle": 2,
        "point": 1,
    }


# a mixed older archive preserves its circle and rectangles in the same sketch
def TestLegacyMixed() -> None:
    Document = OpenDocument(KLegacyPart, include_brep=False, include_tessellation=False)
    assert not Document.validate()
    (Sketch,) = tuple(Value for Value in Document.sketches if Value.name == "Croquis7")
    assert sorted(len(LoopValue) for LoopValue in Sketch.closed_profile_entity_ids) == [
        1,
        4,
        4,
        4,
        4,
    ]
    assert sum(str(Entity.kind) == "circle" for Entity in Sketch.entities) == 1


# the default public path must keep exact geometry and history in generated siblings
def TestPrismOpen(TmpPath: FilePath) -> None:
    Stage = TmpPath / "PartitionProbe"
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            "re/tooling/sw2026/AssemblyPartitionProbe.py",
            str(Stage),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Index = CastValue(
        dict[str, list[dict[str, object]]],
        LoadJson((Stage / "Index.json").read_bytes()),
    )
    Cases = Index["cases"]
    assert len(Cases) == 3
    assert all(CaseRow["sdk_strict_cacheless_geometry"] is True for CaseRow in Cases)
    assert all(
        CaseRow["present_empty_partition_error"]
        == "SLDPRT contains no readable Parasolid payload"
        for CaseRow in Cases
    )
    assert all(CaseRow["sdk_strict_sketch_semantics"] is True for CaseRow in Cases)
    assert all(CaseRow["sdk_strict_summary_bounds"] is True for CaseRow in Cases)


# a generated reversed boss must read through public geometry and history using the signed extent on its actual datum
def TestSignedTop(TmpPath: FilePath) -> None:
    Lengths = (15.0, 23.0, 4.0)
    Source = MakePlainDoc("TopBox", *Lengths)
    Frame = Transform(
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, -1.0),
        SpaceVector(0.0, 1.0, 0.0),
    )
    Model = LowerBoxModel(
        ReplaceValue(
            Source,
            support_planes=(
                ReplaceValue(
                    Source.support_planes[0], name="XZ-plane", transform=Frame
                ),
            ),
        ),
        "TopBox",
        ("length", "width", Source.parameters[0].id),
        Lengths,
        ("Length", "Width", "Height"),
        "Box",
        TopAttached=True,
    )
    Candidate = MakeOriginBox(
        Model,
        r"C:\Kit\TopBox.SLDPRT",
        1740000000,
        PartTextInput({}, {}, {}),
        TopAttached=True,
    )
    OutputPath = TmpPath / "TopBox.SLDPRT"
    _ = OutputPath.write_bytes(Candidate.BytesValue)
    Readback = OpenDocument(OutputPath, include_tessellation=False)
    assert not Readback.validate()
    assert Readback.brep is not None
    (BodyValue,) = Readback.bodies
    assert BodyValue.name == "Box"
    assert (
        BodyValue.topology.volume,
        BodyValue.topology.surface_area,
        BodyValue.topology.face_count,
        BodyValue.topology.edge_count,
        BodyValue.topology.vertex_count,
    ) == (1380.0, 994.0, 6, 12, 8)
    assert {Driver.name: Driver.value.value for Driver in Readback.parameters} == {
        "Length": 15.0,
        "Width": 23.0,
        "Height": 4.0,
    }
    History = OpenDocument(OutputPath, include_brep=False, include_tessellation=False)
    for Current in (Readback, History):
        Bounds = Current.bodies[0].topology.bounding_box
        assert Bounds is not None
        assert Bounds.minimum == SpaceVector(0.0, -4.0, 0.0)
        assert Bounds.maximum == SpaceVector(15.0, 0.0, 23.0)
