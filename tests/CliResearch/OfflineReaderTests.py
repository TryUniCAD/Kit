from json import loads as LoadJson
from os import environ as KEnvironment, pathsep as KPathSeparator
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchRoot import ResearchRoot


# offline decoding must preserve real reader evidence without attempting application verification
def CheckOffline(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    Target = TmpPath / "Decoded"
    Result = RunProcess(
        [
            KPythonPath,
            "-m",
            "KitCli",
            "research",
            "--offline",
            "--root",
            str(RootPath),
            "solidworks",
            "--asset",
            KSwAsset,
            "--output",
            str(Target),
        ],
        cwd=RootPath,
        env={
            **KEnvironment,
            "PYTHONPATH": str(RootPath / "src")
            + KPathSeparator
            + str(RootPath / "Cli"),
        },
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert Result.returncode == 0, Result.stderr
    assert "native verification pending" in Result.stderr
    assert not (Target / "NativeVerification.json").exists()
    Receipt = LoadJson((Target / "receipt.json").read_bytes())
    assert Receipt["native_acceptance"] == "not_established"
    assert Receipt["portable_complete"] is False
    assert LoadJson((Target / "document.json").read_bytes())["$type"] == "CadDocument"
