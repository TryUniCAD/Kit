from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe


# the request builder must preserve its ordinary external command and publication boundary
def RunRequest(WorkPath: FilePath) -> CompletedProcess[str]:
    RootPath = FilePath(__file__).resolve().parents[5]
    ProgramPath = RootPath / "re/automation/P03CandidateRequest.py"
    return RunProcess(
        [
            PythonExe,
            "-I",
            "-B",
            str(ProgramPath),
            "--source-json",
            str(WorkPath / "Source.json"),
            "--logical-json",
            str(WorkPath / "Logical.json"),
            "--output",
            str(WorkPath / "Request.json"),
        ],
        cwd=WorkPath,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
