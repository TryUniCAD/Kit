from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.Feature.BuildCreator import BuildCreator, KCreatorCases
from tests.convert.Commands.Feature.BuildModifier import BuildModifier
from tests.convert.Commands.Feature.ModifierCases import KModifierCases
from tests.convert.Commands.WrapDocument import WrapDocument


@TestMark.parametrize("RecordKind", (*KModifierCases, *KCreatorCases))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckPrereqs(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = (
        BuildModifier(RecordKind)
        if RecordKind in KModifierCases
        else BuildCreator(RecordKind)
    )
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteFeature", HasOutput, TmpPath)


@TestMark.parametrize("IsNested", (False, True))
def CheckTwoInputs(IsNested: bool, TmpPath: FilePath) -> None:
    Document = BuildModifier("CombineValid")
    Document.AssertValid()
    assert len(set(Document.feature_timeline[-1].input_feature_ids)) == 2
    if IsNested:
        Document = WrapDocument(Document)
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "combine.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original
