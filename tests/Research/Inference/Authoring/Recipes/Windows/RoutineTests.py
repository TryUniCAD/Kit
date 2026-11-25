from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe, platform as KPlatform

from pytest import mark as CaseMark

from tests.Research.SupervisorClient import KRepoRoot


# native owner transport must reject stopped processes and stale revisions at the actual interpreter boundary
@CaseMark.skipif(KPlatform != "win32", reason="Windows process identity boundary")
def CheckRoutine(TmpPath: FilePath) -> None:
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/BatchEvidence/ProbeRoutineTransport.py"),
            "check",
            str(TmpPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    assert "transport custody and stopped owner checks passed" in Result.stdout
