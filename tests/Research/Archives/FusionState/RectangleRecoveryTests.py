from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# real native controls must pass both public reader surfaces while malformed and unsupported files retain their refusals
def CheckRecovery(TmpPath: FilePath) -> None:
    RepoPath = FilePath(__file__).resolve().parents[4]
    ReportPath = TmpPath / "Recovery.json"
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            "re/Fusion/RectangleRecovery/VerifyRecovery.py",
            "--output",
            str(ReportPath),
        ],
        cwd=RepoPath,
        capture_output=True,
        timeout=180,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode(errors="replace")
    Report = LoadJson(ReportPath.read_text())
    assert Report["status"] == "passed" and len(Report["positives"]) == 8
    assert len(Report["negative_cases"]) == 14
    assert len(Report["drafted_controls"]) == 4
    assert Report["native_conversion_acceptance"] is False
