from __future__ import annotations

from json import dumps as DumpJson
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# separate interpreters expose hidden document reads and cached graph state during camera construction
def RunCamera(Request: dict[str, object]) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/CameraProcess.py"),
            str(KRepoRoot),
        ],
        input=DumpJson(Request),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
