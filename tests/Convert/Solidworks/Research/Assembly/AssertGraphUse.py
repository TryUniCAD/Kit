from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Assembly.CheckCmgrUse import CheckCmgrUse
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# generated assemblies need completed schema admission through their actual linked reader
def AssertGraphUse(ParentPath: FilePath, ChildPath: FilePath) -> None:
    for InputPath in (ParentPath, ChildPath):
        ReportPath = InputPath.with_suffix(".proven.json")
        assert not ReportPath.exists()
        Outcome = RunProcess(
            [
                PythonExec,
                str(KRepoRoot / "re/tooling/sw2026/serial/RoundTrip.py"),
                str(InputPath),
                "Contents/Config-0,Contents/CMgr,Contents/Config-0-ResolvedFeatures",
                "--link-config",
                "--require-proven",
                "--report",
                str(ReportPath),
            ],
            cwd=KRepoRoot,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = ReadObject(ReportPath)
        assert Report["passed"] is Report["proven_schemas"] is True
        assert Report["byte_identity_passed"] is Report["require_proven"] is True
        assert Report["used_provisional_schemas"] == []
        CheckCmgrUse(Report)
