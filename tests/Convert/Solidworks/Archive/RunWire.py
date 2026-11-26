from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# fresh interpreters must resolve the same repository even from temporary directories
KRepoRoot = FilePath(__file__).resolve().parents[4]


# a dedicated command exposes only synthetic records to the process integration
KWireScript = KRepoRoot / "re/tooling/sw2026/ArchiveWireProcess.py"


# a process boundary keeps the reader independent from the writer cursor and objects
def RunWire(
    ModeName: str, InputPath: FilePath, OutputPath: FilePath
) -> CompletedProcess[str]:
    return RunProcess(
        [PythonExec, "-B", str(KWireScript), ModeName, str(InputPath), str(OutputPath)],
        cwd=InputPath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
