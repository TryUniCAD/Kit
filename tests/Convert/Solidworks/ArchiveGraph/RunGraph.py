from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExec

# resolving the entry point before spawning keeps temporary workspaces independent
KGraphScript = (
    FilePath(__file__).resolve().parents[4] / "re/tooling/sw2026/ArchiveGraphProcess.py"
)


# two fresh interpreters prevent object identities from leaking between the proof directions
def RunGraph(
    ModeName: str, InputPath: FilePath, OutputPath: FilePath
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExec,
            "-B",
            str(KGraphScript),
            ModeName,
            str(InputPath),
            str(OutputPath),
        ],
        cwd=InputPath.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
