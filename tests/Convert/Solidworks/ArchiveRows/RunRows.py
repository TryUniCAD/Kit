from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# the command must resolve the checkout from a separate output directory
KRowsProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckCountedRows.py"
)


# distinct interpreters prevent writer fields and scopes from reaching the reader
def RunRows(
    ModeName: str,
    SourcePath: FilePath,
    OutputPath: FilePath,
    ExtraArgs: tuple[str, ...] = (),
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KRowsProbe),
            ModeName,
            str(SourcePath),
            str(OutputPath),
            *ExtraArgs,
        ],
        cwd=SourcePath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
