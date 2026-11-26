from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# separate processes must locate the checked out codec from the fixture directory
KManagerProbe = (
    FilePath(__file__).resolve().parents[4]
    / "re/tooling/sw2026/CheckManagerDirectory.py"
)


# a new interpreter consumes the actual bytes instead of sharing a graph with the writer
def RunMgrWire(
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
            str(KManagerProbe),
            ModeName,
            str(SourcePath),
            str(OutputPath),
            *ExtraArgs,
        ],
        cwd=OutputPath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
