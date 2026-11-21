from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec
from typing import Literal

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot


# real generated files must cross the declared command boundary before typed graph assertions
def RunConfigTool(
    ToolName: Literal["CheckSdkConfig.py", "CheckConfigBridge.py"],
    InputPaths: tuple[FilePath, ...],
    ReportPath: FilePath,
    Options: tuple[str, ...] = (),
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-B",
            str(KRepoRoot / "re/tooling/sw2026/serial" / ToolName),
            *(str(InputPath) for InputPath in InputPaths),
            "--report",
            str(ReportPath),
            *Options,
        ],
        cwd=KRepoRoot,
        env={**Environment, "PYTHONPATH": str(KRepoRoot / "src")},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
