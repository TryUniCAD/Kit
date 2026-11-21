from json import dumps as DumpJson
from pathlib import Path
from subprocess import run as RunProcess
from sys import executable as PythonPath


# invalid neutral construction choices must fail before a complete drawing artifact crosses the process boundary
def RunModelReject(Request: dict[str, object], ProbeName: str) -> None:
    RootValue = Path(__file__).resolve().parents[6]
    WorkerPath = RootValue / "re/tooling/sw2026/DrawingModelProcess.py"
    JobValue = {
        "schema": "kit.sw2026.sdk-drawing-model-process.v1",
        "request": Request,
        "qualification_probe": ProbeName,
    }
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
    assert "drawing root constructor" in Process.stderr
