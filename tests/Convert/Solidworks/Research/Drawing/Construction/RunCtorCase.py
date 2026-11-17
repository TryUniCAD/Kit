from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# sheet graph evidence must include complete file construction and readback in an isolated process
def RunCtorCase(Request: dict[str, object]) -> dict[str, object]:
    RepoRoot = FilePath(__file__).resolve().parents[6]
    Outcome = RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(RepoRoot / "re/tooling/sw2026/DrawingSheetConstructionProcess.py"),
        ],
        input=DumpJson(
            {
                "schema": "kit.sw2026.sdk-sheet-construction-process.v1",
                "request": Request,
            },
            sort_keys=True,
        ),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    return CastValue(dict[str, object], LoadJson(Outcome.stdout))
