from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# actual generated headers and constructor outputs must cross a fresh interpreter with no external model file inputs
def RunEpochProbe(RequestValue: dict[str, object]) -> dict[str, object]:
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/HeaderEpochProcess.py"),
        ],
        cwd=KRepoRoot,
        input=DumpJson(RequestValue),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
