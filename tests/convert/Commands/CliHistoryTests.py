from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from tests.convert.Commands.BuildHistory import BuildHistory
from tests.convert.Commands.BuildHistoryAsm import BuildHistoryAsm
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.WrapDocument import WrapDocument


# body or mesh data without feature history must remain inspectable rather than convert successfully
@TestMark.parametrize("RecordKind", ("Brep", "Mesh"))
@TestMark.parametrize("HasParams", (False, True))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckNoHistory(
    RecordKind: str, HasParams: bool, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildHistory(RecordKind, HasParams)
    assert Document.feature_timeline == ()
    assert bool(Document.parameters) is HasParams
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "MissingFeatureHistory", HasOutput, TmpPath)


# assembly component links must not qualify local meshes that lack operation history
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckLocalMesh(IsNested: bool, HasOutput: bool, TmpPath: FilePath) -> None:
    Document = BuildHistoryAsm()
    assert Document.assembly is not None and not Document.assembly.documents
    assert any(Definition.mesh_ids for Definition in Document.assembly.definitions)
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "MissingFeatureHistory", HasOutput, TmpPath)


# parameter documents without local geometry must remain valid conversion inputs
def CheckParamOnly(TmpPath: FilePath) -> None:
    Document = MakeFusionDoc(
        DocumentSpec("Parameter only", "height", 20.0, ProfileKind="parameter")
    )
    Document.AssertValid()
    assert Document.parameters and not Document.feature_timeline
    assert not Document.bodies and not Document.meshes and Document.brep is None
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "parameter.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)["destination_format"] == "interchange.json"
    assert LoadJson(Target.read_text(encoding="utf-8"))["parameters"]
    assert Source.read_text(encoding="utf-8") == Original
