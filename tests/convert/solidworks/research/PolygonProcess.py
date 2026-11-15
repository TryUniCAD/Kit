from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.convert.solidworks.research.Polygon.PolygonProgram import KProgram

# startup needs a stable package root independent of the working directory
KRepoRoot = FilePath(__file__).resolve().parents[4]


# geometry validation needs process isolation from inherited interpreter state
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
