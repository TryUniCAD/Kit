from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Convert.Commands.CliProcess import CliProcess


# focused discovery must preserve direction limits when users select an input alias
@TestMark.parametrize(
    "FormatName", ("solidworks.sldprt", "solidworks.sldasm", "SOLIDWORKS.SLDASM")
)
def CheckFormatName(FormatName: str, TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "formats", FormatName, "--json")
    assert Result.returncode == 0, Result.stderr
    assert Result.stderr == ""
    Formats = LoadJson(Result.stdout)
    assert len(Formats) == 1
    assert Formats[0]["format"] == "solidworks.sldprt"
    assert Formats[0]["aliases"] == ["solidworks.sldasm"]
    assert Formats[0]["write_extensions"] == [".sldprt"]
    assert Formats[0]["write_aliases"] == []
    assert list(TmpPath.iterdir()) == []


# unknown format names must provide recovery instead of an empty successful lookup
def CheckUnknownFmt(TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "formats", "missing.format", "--json")
    assert Result.returncode == 1 and Result.stdout == ""
    Error = LoadJson(Result.stderr)
    assert Error["error"] == "ValueError"
    assert "kit formats" in Error["message"]
    assert "missing.format" in Error["message"]
    assert list(TmpPath.iterdir()) == []


# human discovery must expose aliases without suggesting every registered route is qualified
def CheckFormatText(TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "formats", "solidworks.sldasm")
    assert Result.returncode == 0, Result.stderr
    Lines = Result.stdout.splitlines()
    Fields = Lines[0].split("\t")
    Values = [LoadJson(Value) for Value in Lines[1].split("\t")]
    Format = dict(zip(Fields, Values, strict=True))
    assert Format["aliases"] == ["solidworks.sldasm"]
    assert Format["write_aliases"] == []
    assert Format["write_extensions"] == [".sldprt"]
    assert "Registry metadata only" in Lines[2]
    HelpResult = CliProcess(TmpPath, "formats", "--help")
    assert HelpResult.returncode == 0, HelpResult.stderr
    assert "FORMAT" in HelpResult.stdout
    assert "not qualified feature or conversion support" in HelpResult.stdout


# shared alias normalization must apply to focused lookup without changing canonical output
def CheckFusionName(TmpPath: FilePath) -> None:
    Result = CliProcess(TmpPath, "formats", "F3D", "--json")
    assert Result.returncode == 0, Result.stderr
    Formats = LoadJson(Result.stdout)
    assert len(Formats) == 1 and Formats[0]["format"] == "fusion.f3d"
    assert "f3d" in Formats[0]["aliases"]
