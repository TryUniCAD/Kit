from __future__ import annotations

from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactDirs import ReportDir
from tests.Convert.Solidworks.Research.ArtifactIO.ArtifactPaths import ArtifactFile
from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# assembly discovery fixtures need full archive checks while preserving their measured warning state
def TestAsmSources(TmpPath: FilePath) -> None:
    OutputRoot = ReportDir(TmpPath, "SourceParser", "Assembly")
    OutputRoot.mkdir(parents=True, exist_ok=True)
    ReportPath = ArtifactFile(OutputRoot, "Discovery.json")
    Outcome = RunProcess(
        [
            PythonExec,
            str(KRepoRoot / "re/tooling/sw2026/serial/AssemblySources.py"),
            "--report",
            str(ReportPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["passed"] is True and Report["comparison_count"] == 21
    assert Report["native_acceptance"] is Report["heldout_payloads_read"] is False
    assert Report["writer_output_count"] == 0
