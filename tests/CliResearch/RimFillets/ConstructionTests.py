from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from pytest import approx as ApproxValue, mark as TestMark

from tests.CliResearch.ResearchRoot import ResearchRoot
from tests.CliResearch.RimFillets.CaseNames import KCaseNames


# source free native generation must match independent vendor measurements through a fresh process
@TestMark.parametrize("CaseName", KCaseNames)
def CheckRimWriter(TmpPath: FilePath, CaseName: str) -> None:
    RootPath = ResearchRoot()
    PackPath = RootPath / "re/Fusion/RimFilletPack"
    OutputPath = TmpPath / "Replay"
    Result = RunProcess(
        [
            KPythonPath,
            str(PackPath / "Replay.py"),
            "--root",
            str(RootPath),
            "--cases",
            str(PackPath / "Cases.json"),
            "--case",
            CaseName,
            "--directory",
            str(OutputPath),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    Report = LoadJson((OutputPath / "Replay.json").read_bytes())
    Native = LoadJson(
        (PackPath / "Measurements" / CaseName / "Author.json").read_bytes()
    )
    (BodyValue,) = Native["initial"]["bodies"]
    assert Report["model_equal"] is True
    Geometry = Report["geometry"]
    assert Geometry["VolumeCm"] == ApproxValue(BodyValue["volume_cm3"], rel=1e-7)
    assert Geometry["AreaCm"] == ApproxValue(BodyValue["area_cm2"], rel=1e-7)
    assert (Geometry["FaceCount"], Geometry["EdgeCount"], Geometry["VertexCount"]) == (
        BodyValue["faces"],
        BodyValue["edges"],
        BodyValue["vertices"],
    )
    assert Geometry["LowerCm"] == ApproxValue(BodyValue["min_cm"], abs=1e-7)
    assert Geometry["UpperCm"] == ApproxValue(BodyValue["max_cm"], abs=1e-7)
    assert Report["native_acceptance"] is False
