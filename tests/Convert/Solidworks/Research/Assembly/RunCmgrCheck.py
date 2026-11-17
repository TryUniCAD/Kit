from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# the shared manager codec must run through its real file and command boundary
def RunCmgrCheck(
    InputPaths: tuple[FilePath, ...], ReportPath: FilePath
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/serial/CheckSdkCmgr.py"),
            *(str(InputPath) for InputPath in InputPaths),
            "--report",
            str(ReportPath),
        ],
        cwd=KRepoRoot,
        env={**Environment, "PYTHONPATH": str(KRepoRoot / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
