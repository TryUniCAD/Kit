from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe


# the paired source proof and replay must cross the actual tool process boundary
def RunIntentStep(WorkPath: FilePath, *Arguments: str) -> CompletedProcess[str]:
    RootPath = FilePath(__file__).resolve().parents[4]
    ScriptPath = RootPath / "re/automation/P03ConstraintIntent.py"
    return RunProcess(
        [PythonExe, "-I", "-B", str(ScriptPath), *Arguments],
        cwd=WorkPath,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
