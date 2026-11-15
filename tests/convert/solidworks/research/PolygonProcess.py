from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.convert.solidworks.research.PolygonProgram import KProgram

KRepoRoot = FilePath(__file__).resolve().parents[4]


def RunPolygon(
    *, Directory: FilePath, Scenario: str, Count: int, Depth: float
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-c",
            KProgram,
            str(KRepoRoot),
            Scenario,
            str(Count),
            str(Depth),
        ],
        cwd=Directory,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
