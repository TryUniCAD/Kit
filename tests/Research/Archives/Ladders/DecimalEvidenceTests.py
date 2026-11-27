from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# the retained corpus must verify through its real process boundary before other readers reuse it
def CheckEvidence(TmpPath: FilePath) -> None:
    RepoPath = FilePath(__file__).resolve().parents[4]
    ReportPath = TmpPath / "Evidence.json"
    Result = RunProcess(
        [
            PythonExe,
            str(RepoPath / "re/NativePlacement2026/Verify.py"),
            "--output",
            str(ReportPath),
        ],
        cwd=RepoPath,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    Report = LoadJson(ReportPath.read_text())
    assert Report["status"] == "passed"
    assert Report["native_files"] == 143
    assert Report["missing_native_files"] == 1
    assert Report["candidate270_comparisons"] == 138
