from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.Commands.CliProcess import CliProcess


def CheckAsmLabel(TmpPath: FilePath) -> None:
    Source = (
        KSamplePath.parents[1]
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "Cylinder Head Assy 1.SLDASM"
    )
    Result = CliProcess(TmpPath, "decode", str(Source), "--layer", "container")
    assert Result.returncode == 0, Result.stderr
    assert LoadJson(Result.stdout)["format"] == "solidworks.sldasm"
    Renamed = TmpPath / "assembly.data"
    _ = Renamed.write_bytes(Source.read_bytes())
    Explicit = CliProcess(
        TmpPath,
        "decode",
        str(Renamed),
        "--layer",
        "container",
        "--from",
        "solidworks.sldasm",
    )
    assert Explicit.returncode == 0, Explicit.stderr
    assert LoadJson(Explicit.stdout)["format"] == "solidworks.sldasm"


@TestMark.parametrize("HasOutput", (False, True))
def CheckAsmSources(HasOutput: bool, TmpPath: FilePath) -> None:
    Fixture = (
        KSamplePath.parents[1]
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "ENSAMBLAJE DE SEGURO DE ARBOL DE LEVAS.SLDASM"
    )
    Source = TmpPath / "isolated.SLDASM"
    Original = Fixture.read_bytes()
    _ = Source.write_bytes(Original)
    Decoded = CliProcess(TmpPath, "decode", str(Source), "--partial")
    assert Decoded.returncode == 0, Decoded.stderr
    Assembly = LoadJson(Decoded.stdout)["document"]["assembly"]
    RootId = Assembly["root_definition_id"]
    RootDef = next(
        Definition
        for Definition in Assembly["definitions"]
        if Definition["id"] == RootId
    )
    assert RootDef["attributes"]["source_resolved"] is True
    Unloaded = [
        Definition
        for Definition in Assembly["definitions"]
        if Definition["id"] != RootId
    ]
    assert Unloaded and Assembly["documents"] == []
    assert all(
        Definition["attributes"]["source_resolved"] is False
        and Definition["document_id"] == ""
        for Definition in Unloaded
    )
    Target = TmpPath / "blocked.json"
    if HasOutput:
        _ = Target.write_bytes(b"existing output")
    Result = CliProcess(
        TmpPath, "convert", str(Source), str(Target), "--overwrite", "--json"
    )
    assert Result.returncode == 1 and Result.stdout == ""
    assert "error" in LoadJson(Result.stderr)
    assert Source.read_bytes() == Original and Target.exists() is HasOutput
    if HasOutput:
        assert Target.read_bytes() == b"existing output"
