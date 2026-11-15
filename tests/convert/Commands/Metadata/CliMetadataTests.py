from dataclasses import replace as ReplaceData
from hashlib import sha256 as HashContent
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.Metadata.BuildMetadata import BuildMetadata, KMetadataCases
from tests.convert.Commands.WrapDocument import WrapDocument


@TestMark.parametrize("RecordKind", KMetadataCases)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckRetained(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildMetadata(RecordKind)
    assert Document.bodies and Document.feature_timeline[-1].definition is not None
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "RetainedMetadata", HasOutput, TmpPath)


@TestMark.parametrize("IsNested", (False, True))
def CheckProvenance(IsNested: bool, TmpPath: FilePath) -> None:
    Document = ReplaceData(
        MakeFusionDoc(DocumentSpec("Typed provenance history", "height", 20.0)),
        metadata={
            "source_sha256": HashContent(KSamplePath.read_bytes()).hexdigest(),
            "source_path": "original.SLDPRT",
            "source_format": "solidworks.sldprt",
            "notes": {
                "tags": ("research", "provenance"),
                "revision": "source-revision",
            },
        },
    )
    Document.AssertValid()
    if IsNested:
        Document = WrapDocument(Document)
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "provenance.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original
