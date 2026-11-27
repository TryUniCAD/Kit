from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath

from tests.Research.SupervisorClient import SessionHost


# compatibility rejection must target an implementation that can otherwise dispatch the unchanged queued job
def ProveLegacy(Harness: SessionHost, RootPath: FilePath) -> None:
    ResultInfo = RunProcess(
        [
            KPythonPath,
            str(RootPath / "re/automation/Supervisor.py"),
            "--config",
            str(Harness.ConfigFile),
            "run",
            "--idle-seconds",
            "0.2",
            "--max-seconds",
            "20",
        ],
        cwd=RootPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == 0, (ResultInfo.stdout, ResultInfo.stderr)
    assert Harness.ReadJob("windows:legacy")["state"] == "completed"
