from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.convert.solidworks.research.Model.ModelProgram import KProgram

# repository discovery must remain stable because the child process starts in an empty directory
KRepoRoot = FilePath(__file__).resolve().parents[4]


# a fresh isolated interpreter prevents local caches and working directory fixtures from supplying constructor data
def RunBuilders(
    Directory: FilePath, Count: int, Density: float, Prefix: str
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-c",
            KProgram,
            str(KRepoRoot),
            str(Count),
            str(Density),
            Prefix,
        ],
        cwd=Directory,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
