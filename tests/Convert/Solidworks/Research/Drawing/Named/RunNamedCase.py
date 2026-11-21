from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path
from subprocess import run as RunProcess
from sys import executable as PythonPath
from typing import cast as CastValue


# every named profile must serialize in a fresh process without borrowing a previous class map or document state
def RunNamedCase(JobValue: dict[str, object]) -> dict[str, object]:
    RootValue = Path(__file__).resolve().parents[6]
    WorkerPath = RootValue / "re/tooling/sw2026/DrawingNamedDefinitionProcess.py"
    Process = RunProcess(
        [PythonPath, "-I", "-B", str(WorkerPath)],
        input=DumpJson(JobValue, allow_nan=False),
        text=True,
        capture_output=True,
        cwd=RootValue,
        timeout=120,
        check=False,
    )
    assert Process.returncode == 0, Process.stderr
    assert not Process.stderr
    return CastValue(dict[str, object], LoadJson(Process.stdout))
