from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# original cad files and receipts must remain independently verifiable without a licensed application
def CheckRecovery(TmpPath: FilePath) -> None:
    RepoPath = FilePath(__file__).resolve().parents[4]
    ReportPath = TmpPath / "Recovery.json"
    Result = RunProcess(
        [
            PythonExe,
            "re/solidworks/FeatureLadderRecovery/Verify.py",
            "--output",
            str(ReportPath),
        ],
        cwd=RepoPath,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode(errors="replace")
    Report = LoadJson(ReportPath.read_text())
    assert Report["status"] == "passed"
    assert Report["strict_success_files"] == 111
    assert Report["centroid_mismatches_retained"] == 96
    assert Report["native_conversion_acceptance"] is False
