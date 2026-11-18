from json import dumps as DumpJson
from pathlib import Path
from subprocess import run as RunProcess
from sys import executable as PythonPath


# unsupported portable content and invalid typed construction settings must fail before any candidate artifact is returned
def RunBlankReject(JobValue: dict[str, object]) -> None:
    RootValue = Path(__file__).resolve().parents[6]
    WorkerPath = RootValue / "re/tooling/sw2026/DrawingSdkProcess.py"
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
    assert "blank drawing constructor rejected" in Process.stderr
