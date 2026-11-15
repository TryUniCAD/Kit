from __future__ import annotations

from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue

KRepoRoot = FilePath(__file__).resolve().parents[4]
KProgram = FilePath(__file__).with_name("FreshPartProcess.py")


def RunFreshPart(Request: dict[str, object]) -> dict[str, object]:
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(KProgram), str(KRepoRoot)],
        input=DumpJson(Request),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
