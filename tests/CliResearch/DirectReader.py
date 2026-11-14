from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


def DirectReader(
    WorkPath: FilePath, ScriptName: str, *Arguments: str
) -> CompletedProcess[str]:
    RootPath = ResearchRoot()
    return RunProcess(
        (
            KPythonPath,
            str(RootPath / "re/automation" / ScriptName),
            "--root",
            str(RootPath),
            *Arguments,
        ),
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
