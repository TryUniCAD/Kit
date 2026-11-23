from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe

# subprocess coverage must use the programme belonging to the collected checkout
KRepoRoot = FilePath(__file__).resolve().parents[4]


# bulk checks exercise actual command parsing file loading matching and publication together
def RunBulk(Arguments: list[str]) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/CompareDecoded.py"),
            "--left-unit",
            "mm",
            "--right-unit",
            "mm",
            *Arguments,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
