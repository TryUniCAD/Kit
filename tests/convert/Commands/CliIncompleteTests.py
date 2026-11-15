from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.Commands.BuildIncomplete import BuildIncomplete
from tests.convert.Commands.BuildNativeBrep import BuildNativeBrep
from tests.convert.Commands.CheckJsonBlock import CheckJsonBlock
from tests.convert.Commands.CliProcess import CliProcess
from tests.convert.Commands.WrapDocument import WrapDocument


# unresolved component evidence must block publication across root and nested assembly documents
@TestMark.parametrize(
    "RecordKind",
    (
        "NativeCurve",
        "NativePcurve",
        "NativeSurface",
        "MissingReference",
        "ExternalReference",
        "UnrepresentedPart",
        "NativeComponent",
        "SourceUnresolved",
        "SourceDeferred",
        "TransformUnresolved",
        "NativeTransforms",
        "NativeConstraints",
    ),
)
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckUnready(
    RecordKind: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    IsGeometry = RecordKind in ("NativeCurve", "NativePcurve", "NativeSurface")
    Document = (
        BuildNativeBrep(RecordKind) if IsGeometry else BuildIncomplete(RecordKind)
    )
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(
        Document, RecordKind if IsGeometry else "IncompleteAssembly", HasOutput, TmpPath
    )


# resolved placement graphs still need qualified assembly history while empty assemblies remain eligible
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("OwnerName", ("", "root", "subassembly"))
@TestMark.parametrize(
    "RecordKind", ("ResolvedReference", "ProvenanceOnly", "EmptyAssembly")
)
def CheckResolved(
    IsNested: bool, OwnerName: str, RecordKind: str, TmpPath: FilePath
) -> None:
    Document = BuildIncomplete(RecordKind, OwnerName)
    if IsNested:
        Document = WrapDocument(Document)
    Document.AssertValid()
    if IsNested or RecordKind != "EmptyAssembly":
        CheckJsonBlock(Document, "UnqualifiedAssembly", False, TmpPath)
        return
    Source = TmpPath / "source.json"
    Original = Document.to_json()
    _ = Source.write_text(Original, encoding="utf-8")
    Target = TmpPath / "resolved.json"
    Result = CliProcess(TmpPath, "convert", str(Source), str(Target), "--json")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)["destination_format"] == "interchange.json"
    assert LoadJson(Target.read_text(encoding="utf-8")) == LoadJson(Original)
    assert Source.read_text(encoding="utf-8") == Original


# every assembly graph owner must resolve child references before conversion can publish
@TestMark.parametrize("OwnerName", ("root", "subassembly"))
@TestMark.parametrize("IsNested", (False, True))
@TestMark.parametrize("HasOutput", (False, True))
def CheckGraphChild(
    OwnerName: str, IsNested: bool, HasOutput: bool, TmpPath: FilePath
) -> None:
    Document = BuildIncomplete("MissingReference", OwnerName)
    if IsNested:
        Document = WrapDocument(Document)
    CheckJsonBlock(Document, "IncompleteAssembly", HasOutput, TmpPath)
