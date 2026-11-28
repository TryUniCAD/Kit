from hashlib import file_digest as FileDigest
from json import loads as LoadJson
from os import environ as KEnvironment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonPath

from tests.CliResearch.Reports.ScopeLayerEvidence import VerifyLayerPins
from tests.CliResearch.ResearchRoot import ResearchRoot


# a real saved corner cut exposes the missing strict provenance through the same command researchers use
def CheckLayerScope(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    CapturePath = RootPath / "re/Fusion/Reconstruction/BoundaryCuts"
    SourcePath = CapturePath / "Controls/RequestedCorner.f3d"
    SourceSha = LoadJson((CapturePath / "RequestedCorner.json").read_bytes())["sha256"]
    with SourcePath.open("rb") as Stream:
        assert FileDigest(Stream, "sha256").hexdigest() == SourceSha
    RunPath = TmpPath / "CornerScope"
    Result = RunProcess(
        (
            PythonPath,
            "-m",
            "KitCli",
            "run",
            "--root",
            str(RootPath),
            "fusion",
            "--input",
            str(SourcePath),
            "--directory",
            str(RunPath),
            "--workers",
            "1",
            "--reserved-memory-mib",
            "512",
        ),
        cwd=TmpPath,
        env={**KEnvironment, "KIT_NATIVE_API_DIRECTORY": str(TmpPath / "NativeApi")},
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert Result.returncode == 2, Result.stdout + Result.stderr
    VerifyLayerPins(RunPath, SourcePath, SourceSha)
