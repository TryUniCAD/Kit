from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import ReportDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# saved native derivatives must preserve complete critical archives and neutral parameter edits across a process boundary
def TestSavedCircle(TmpPath: FilePath) -> None:
    OutputRoot = ReportDir(TmpPath, "SourceParser", "Curve", "SavedCircles")
    OutputRoot.mkdir(parents=True, exist_ok=True)
    ReportPath = ArtifactFile(OutputRoot, "Checked.json")
    Outcome = RunProcess(
        [
            PythonExec,
            str(KRepoRoot / "re/tooling/sw2026/serial/SavedCircles.py"),
            "--report",
            str(ReportPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    for Suffix, TextValue in (
        (".stdout.log", Outcome.stdout),
        (".stderr.log", Outcome.stderr),
    ):
        LogPath = ArtifactFile(OutputRoot, ReportPath.with_suffix(Suffix).name)
        Written = LogPath.write_text(TextValue, encoding="utf-8")
        assert Written == len(TextValue)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["passed"] is True
    assert Report["file_count"] == 6 and Report["stream_count"] == 54
    assert Report["numeric_count"] == 108
    assert (
        Report["is_writer_output"]
        is Report["native_acceptance_inherited"]
        is Report["heldout_native_payloads_read"]
        is False
    )
