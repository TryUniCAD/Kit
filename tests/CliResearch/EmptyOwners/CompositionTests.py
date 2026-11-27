from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from tests.CliResearch.EmptyOwners.OwnerRoots import OwnerRoots
from tests.CliResearch.ResearchRoot import ResearchRoot


# maintained planner coverage must exercise the actual three request command and its unsupported input refusal
def CheckCompose(TmpPath: FilePath) -> None:
    RootPath = ResearchRoot()
    ScriptPath = RootPath / "re/solidworks/RendererBoundary/CheckEmptyOwnersCli.py"
    with OwnerRoots(RootPath, TmpPath) as (ReaderRoot, PropertyRoot):
        Result = RunProcess(
            (
                KPythonPath,
                "-I",
                "-B",
                str(ScriptPath),
                "--dependency-root",
                str(ReaderRoot),
                "--property-root",
                str(PropertyRoot),
                "--output",
                str(TmpPath / "Smoke"),
            ),
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    assert Result.returncode == 0, Result.stderr + Result.stdout
