from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath

from tests.CliResearch.ResearchRoot import ResearchRoot


def ResearchCli(
    WorkPath: FilePath, ToolName: str, *Arguments: str
) -> CompletedProcess[str]:
    return RunProcess(
        (
            KPythonPath,
            "-I",
            "-m",
            "convert",
            "research",
            "--root",
            str(ResearchRoot()),
            ToolName,
            *Arguments,
        ),
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
