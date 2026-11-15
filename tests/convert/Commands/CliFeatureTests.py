from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import Literal

from pytest import mark as TestMark

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from tests.convert.Commands.BuildBadStep import BuildBadStep, KBadKinds
from tests.convert.Commands.BuildSketchGeom import BuildSketchGeom
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.WrapDocument import WrapDocument


@TestMark.parametrize("RecordKind", tuple(KBadKinds))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckBadStep(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildBadStep(RecordKind)
    assert Document.bodies and Document.feature_timeline
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


@TestMark.parametrize("RecordKind", ("Brep", "Mesh"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckSketchGeom(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildSketchGeom(RecordKind)
    assert Document.feature_timeline and not Document.bodies
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


@TestMark.parametrize("ProfileKind", ("circle", "rectangle"))
@TestMark.parametrize("IsNested", (False, True))
def CheckSketchOnly(
    ProfileKind: Literal["circle", "rectangle"], IsNested: bool, TmpPath: FilePath
) -> None:
    Document = MakeFusionDoc(
        DocumentSpec("Typed sketch", "length", 20.0, ProfileKind=ProfileKind)
    )
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "sketch.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original
