from __future__ import annotations

from os import getenv as ReadEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from tests.Convert.Solidworks.Research.ArchiveProcess import KRepoRoot
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject


# native saved derivatives must preserve complete archives and independently measured editable state
def TestTreeSaves(TmpPath: FilePath) -> None:
    OutputRoot = (
        FilePath(ReadEnv("SwResearchOutput") or str(TmpPath))
        / "SourceParser/Curve/TreeSaves"
    )
    OutputRoot.mkdir(parents=True, exist_ok=True)
    ReportPath = OutputRoot / "Checked.json"
    Outcome = RunProcess(
        [
            PythonExec,
            str(KRepoRoot / "re/tooling/sw2026/serial/TreeSaves.py"),
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
        Written = ReportPath.with_suffix(Suffix).write_text(TextValue, encoding="utf-8")
        assert Written == len(TextValue)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = ReadObject(ReportPath)
    assert Report["passed"] is True
    assert Report["file_count"] == 6
    assert Report["stream_count"] == 54
    assert Report["semantic_check_count"] == 108
    assert Report["pose_check_count"] == 102
    assert (
        Report["is_writer_output"]
        is Report["native_acceptance_inherited"]
        is Report["heldout_native_payloads_read"]
        is False
    )
