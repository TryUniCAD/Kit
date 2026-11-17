from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from typing import cast as CastValue


# complete codec checks must cross a process boundary with runtime input access guarded
def RunDefCase(Request: dict[str, object]) -> dict[str, object]:
    RepoRoot = FilePath(__file__).resolve().parents[6]
    ScriptPath = RepoRoot / "re/tooling/sw2026/DrawingDefinitionProcess.py"
    Outcome = RunProcess(
        [PythonExec, "-I", "-B", str(ScriptPath)],
        input=DumpJson(
            {
                "schema": "kit.sw2026.sdk-drawing-definition-process.v1",
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
