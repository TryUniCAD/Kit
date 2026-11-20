from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# the worker locates the checkout independently of the fixture directory
KBodyValueProbe = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/CheckBodyValues.py"
)


# each process receives its own graph identities and only its file inputs
def RunBodyValues(
    ModeName: str, SourcePath: FilePath, OutputPath: FilePath
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-I",
            "-B",
            str(KBodyValueProbe),
            ModeName,
            str(SourcePath),
            str(OutputPath),
        ],
        cwd=SourcePath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
