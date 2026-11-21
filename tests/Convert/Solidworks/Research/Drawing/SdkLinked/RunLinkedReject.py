from json import dumps as DumpJson
from pathlib import Path
from subprocess import run as RunProcess
from sys import executable as PythonPath


# malformed complete linked intent must fail without artifact output or a hidden runtime dependency
def RunLinkedReject(JobValue: dict[str, object]) -> None:
    RootValue = Path(__file__).resolve().parents[6]
    WorkerPath = RootValue / "re/tooling/sw2026/DrawingSdkLinkedProcess.py"
    Process = RunProcess(
        [PythonPath, "-I", "-B", str(WorkerPath)],
        input=DumpJson(JobValue, allow_nan=False),
        text=True,
        capture_output=True,
        cwd=RootValue,
        timeout=120,
        check=False,
    )
    assert Process.returncode != 0
    assert not Process.stdout
    assert "linked drawing constructor rejected" in Process.stderr
    assert "PermissionError" not in Process.stderr
