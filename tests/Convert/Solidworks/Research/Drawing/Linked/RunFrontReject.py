from json import dumps as DumpJson
from pathlib import Path
from subprocess import run as RunProcess
from sys import executable as PythonPath


# unsupported linked graphs must fail across the process boundary before publishing any output artifact
def RunFrontReject(JobValue: dict[str, object], ProbeName: str) -> None:
    RootValue = Path(__file__).resolve().parents[6]
    WorkerPath = RootValue / "re/tooling/sw2026/DrawingFrontDefinitionProcess.py"
    Process = RunProcess(
        [PythonPath, "-I", "-B", str(WorkerPath)],
        input=DumpJson({**JobValue, "qualification_probe": ProbeName}, allow_nan=False),
        text=True,
        capture_output=True,
        cwd=RootValue,
        timeout=120,
        check=False,
    )
    assert Process.returncode != 0
    assert not Process.stdout
    assert "front drawing Definition" in Process.stderr
