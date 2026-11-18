from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path
from subprocess import run as RunProcess
from sys import executable as PythonPath
from typing import cast as CastValue


# a real process must construct the child and drawing with no inherited archive objects source inputs or research implementation
def RunLinkedCase(
    JobValue: dict[str, object], IsCounterpart: bool = False
) -> dict[str, object]:
    RootValue = Path(__file__).resolve().parents[6]
    WorkerName = (
        "DrawingSdkLinkedCounterpart.py"
        if IsCounterpart
        else "DrawingSdkLinkedProcess.py"
    )
    WorkerPath = RootValue / "re/tooling/sw2026" / WorkerName
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
