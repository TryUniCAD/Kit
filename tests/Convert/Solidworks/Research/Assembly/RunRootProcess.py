from __future__ import annotations

from json import dumps as DumpJson, loads as LoadJson
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# one guarded process boundary preserves the same admission for every assembly request
def RunRootProcess(Request: dict[str, object]) -> dict[str, object]:
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/AssemblyRootProcess.py"),
            str(KRepoRoot),
        ],
        cwd=KRepoRoot,
        input=DumpJson(Request),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
